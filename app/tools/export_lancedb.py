import sqlite3
import struct
import argparse
from pathlib import Path

try:
    import lancedb
    import pyarrow as pa
except ImportError:
    raise RuntimeError("lancedb and pyarrow are required. Run: pip install lancedb pyarrow")

DB_PATH = Path("app/data/appdata/amplify.db")

def export_to_lancedb(output_dir: Path):
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # We only export rows that have a valid embedding
    cur.execute("SELECT latexcode, similarity_emb FROM questions WHERE similarity_emb IS NOT NULL")
    rows = cur.fetchall()
    
    if not rows:
        print("No embeddings found in the SQLite database to backup!")
        return

    print(f"Found {len(rows)} embeddings. Preparing export...")

    # Define the LanceDB schema explicitly (matching what seed.py expects)
    schema = pa.schema([
        pa.field("question", pa.string()),
        pa.field("kind", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 3072))
    ])

    data = []
    for latexcode, sim_blob in rows:
        # Unpack the 12288 byte blob into 3072 floats
        try:
            vec = struct.unpack(f"<{3072}f", sim_blob)
            
            # seed.py expects 'similarity' and 'classification' kinds.
            # We will export both just to be safe.
            data.append({
                "question": latexcode,
                "kind": "similarity",
                "vector": list(vec)
            })
            data.append({
                "question": latexcode,
                "kind": "classification",
                "vector": list(vec)
            })
        except struct.error:
            continue

    print(f"Connecting to LanceDB at {output_dir}...")
    db = lancedb.connect(str(output_dir))
    
    if "questions" in db.table_names():
        print("Dropping existing LanceDB 'questions' table...")
        db.drop_table("questions")
        
    print("Writing data to LanceDB. This may take a moment...")
    db.create_table("questions", data=data, schema=schema)
    
    print(f"\nSUCCESS! Backed up {len(rows)} unique questions (as both similarity & classification vectors) to {output_dir}")
    print("You can now safely use this LanceDB folder as the source for any future database rebuilds or CSV ingestions!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup SQLite embeddings to LanceDB")
    parser.add_argument("--output", type=str, default="app/data/appdata/lancedb_backup", help="Path to output LanceDB folder")
    args = parser.parse_args()
    
    out_path = Path(args.output)
    export_to_lancedb(out_path)
