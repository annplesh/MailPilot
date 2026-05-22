import os
import re

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client

load_dotenv()

FAQ_PATH   = os.getenv("FAQ_PATH", "mailpilot_faq.txt")
TABLE      = "documents"
MODEL_NAME = "all-MiniLM-L6-v2"


def parse_chunks(text: str) -> list[dict]:
    """Return one dict per Q&A pair: {content, question}."""
    chunks = []
    pattern = re.compile(r"^(Q: .+)\n(A: .+)$", re.MULTILINE)
    for m in pattern.finditer(text):
        question = m.group(1)[3:].strip()
        answer   = m.group(2)[3:].strip()
        chunks.append({
            "content":  f"Q: {question}\nA: {answer}",
            "question": question,
        })
    return chunks


def main() -> None:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

    with open(FAQ_PATH, encoding="utf-8") as f:
        text = f.read()

    chunks = parse_chunks(text)
    if not chunks:
        print("No Q&A pairs found — nothing to upload.")
        return

    print(f"Parsed {len(chunks)} chunks. Generating embeddings...")
    model      = SentenceTransformer(MODEL_NAME)
    texts      = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)

    client = create_client(supabase_url, supabase_key)

    rows = [
        {
            "content":   c["content"],
            "embedding": embeddings[i].tolist(),
            "metadata":  {"source": FAQ_PATH, "question": c["question"]},
        }
        for i, c in enumerate(chunks)
    ]

    client.table(TABLE).insert(rows).execute()
    print(f"Uploaded {len(rows)} chunk(s) to '{TABLE}'.")


if __name__ == "__main__":
    main()
