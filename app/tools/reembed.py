"""
Gemini Multimodal Synchronous Re-Embedding Script
-------------------------------------------------
This script iterates through the local database and uses the synchronous
Gemini API to embed the questions and solutions along with their images.
It updates the database in real-time.

It uses `tenacity` for exponential backoff to handle rate limits.
"""

import sqlite3
import struct
import base64
import time
import argparse
import mimetypes
import re
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(".env.local")
except ImportError:
    pass

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
except ImportError:
    raise RuntimeError("The 'tenacity' package is required for rate limit handling. Run: pip install tenacity")


DB_PATH = Path("app/data/appdata/amplify.db")
IMG_DIR = Path("app/data/appdata/teximages")

# Google's multimodal embedding model
MODEL = "models/gemini-embedding-2"
DIMENSIONS = 3072

IMG_PATTERN = re.compile(r'\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}')


def get_client():
    if not genai:
        raise RuntimeError("'google-genai' SDK is required. Run 'pip install google-genai'")
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found in environment or .env.local")
    return genai.Client(api_key=api_key)


def extract_images(latex: str) -> list[Path]:
    """Find all image paths referenced in the LaTeX code."""
    found = []
    if not latex:
        return found
        
    names = IMG_PATTERN.findall(latex)
    for name in names:
        base = name.strip()
        candidates = [IMG_DIR / base, IMG_DIR / f"{base}.png", IMG_DIR / f"{base}.jpg", IMG_DIR / f"{base}.jpeg"]
        for p in candidates:
            if p.exists() and p.is_file():
                if p not in found:
                    found.append(p)
                break
    return found


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"Rate limited or error. Retrying in {retry_state.next_action.sleep} seconds...")
)
def embed_single_item(client, q_latex, s_latex):
    """Calls the Gemini API to embed a single question+solution with its images."""
    q_latex = q_latex or ""
    s_latex = s_latex or ""
    
    task_prefix = "Task: Find problems that share similar underlying concepts, solution techniques, and logical structures.\n\n"
    combined_text = task_prefix + f"Question:\n{q_latex}"
    if s_latex.strip():
        combined_text += f"\n\nSolution:\n{s_latex}"
        
    parts = [combined_text.strip()]
    
    img_paths = extract_images(q_latex) + extract_images(s_latex)
    for p in img_paths:
        try:
            mime, _ = mimetypes.guess_type(str(p))
            mime = mime or "image/png"
            # Using types.Part.from_bytes ensures correct formatting for the SDK
            parts.append(
                types.Part.from_bytes(data=p.read_bytes(), mime_type=mime)
            )
        except Exception as e:
            print(f"Warning: Failed to read image {p}: {e}")

    res = client.models.embed_content(
        model=MODEL,
        contents=parts,
        config=types.EmbedContentConfig(output_dimensionality=DIMENSIONS)
    )
    
    # Depending on the SDK version, the structure is res.embeddings[0].values
    try:
        vec = res.embeddings[0].values
    except Exception:
        # Fallback if structure is different
        vec = getattr(res, "embedding", res).values
        
    return vec


def run_sync():
    print("Starting synchronous embedding process...")
    client = get_client()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # By only selecting rows where similarity_emb IS NULL, the script can seamlessly 
    # resume from exactly where it left off if it gets interrupted.
    cur.execute("SELECT question_id, latexcode, solution FROM questions WHERE similarity_emb IS NULL")
    rows = cur.fetchall()
    
    total = len(rows)
    success = 0
    
    print(f"Found {total} questions. Processing sequentially...")
    
    start_time = time.time()
    for i, (qid, q_latex, s_latex) in enumerate(rows, 1):
        try:
            vec = embed_single_item(client, q_latex, s_latex)
            
            if len(vec) != DIMENSIONS:
                print(f"[{i}/{total}] Warning: Q{qid} got {len(vec)} dims instead of {DIMENSIONS}. Skipping.")
                continue
                
            blob = struct.pack(f"<{DIMENSIONS}f", *vec)
            
            cur.execute(
                "UPDATE questions SET classification_emb = ?, similarity_emb = ? WHERE question_id = ?",
                (blob, blob, qid)
            )
            # Commit every 10 items and print ETA to give frequent feedback
            if i % 10 == 0:
                conn.commit()
                elapsed = time.time() - start_time
                rate = i / elapsed
                eta_sec = (total - i) / rate
                
                hours = int(eta_sec // 3600)
                minutes = int((eta_sec % 3600) // 60)
                seconds = int(eta_sec % 60)
                eta_str = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"
                
                print(f"[{i}/{total}] Saved | Rate: {rate:.2f} it/s | ETA: {eta_str}")
                
            success += 1
            
        except Exception as e:
            print(f"[{i}/{total}] FATAL ERROR on Q{qid} after all retries exhausted: {e}")
            # We can continue or break. Let's continue to the next item.
            continue
            
    conn.commit()
    print(f"Process complete! Successfully embedded {success}/{total} questions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multimodal Synchronous Re-Embedding")
    parser.add_argument("--run", action="store_true", help="Start the embedding process")
    args = parser.parse_args()
    
    if args.run:
        run_sync()
    else:
        print("Run the script with the --run flag to start: python -m app.tools.reembed --run")
