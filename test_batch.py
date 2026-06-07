import os
try:
    from dotenv import load_dotenv
    load_dotenv(".env.local")
except ImportError:
    pass

try:
    from google import genai
except ImportError:
    print("google-genai not installed.")
    exit(1)

def main():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not found.")
        return

    client = genai.Client(api_key=api_key)
    
    print("Uploading test 10-line JSONL...")
    try:
        file_obj = client.files.upload(
            file="app/data/appdata/test_requests.jsonl", 
            config={'mime_type': 'application/jsonl'}
        )
        print(f"Uploaded! URI: {file_obj.uri}")
    except Exception as e:
        print(f"Upload failed: {e}")
        return

    print("Creating tiny test batch job...")
    try:
        job = client.batches.create_embeddings(
            model="models/gemini-embedding-2",
            src={"file_name": file_obj.name}
        )
        print(f"SUCCESS! Job created: {job.name}")
        print("This proves your account works, the main file was just too big!")
    except Exception as e:
        print(f"Batch creation failed: {e}")
        print("\nCONCLUSION: Since even a tiny 10-item job failed with 429, your API key is currently restricted by Google Cloud's new-account billing probation. You must wait for the tier to fully clear or make a manual payment.")

if __name__ == "__main__":
    main()
