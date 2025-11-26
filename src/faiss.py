import faiss
import sqlite3

def build_index(emails):
    dim = 384# TODO: this depends on model
    index = faiss.IndexFlatIP(dim)
    conn = sqlite3.connect("data/meta.sqlite")
    conn.execute("CREATE TABLE IF NOT EXISTS mails (path TEXT PRIMARY KEY, vector BLOB)")

    for e in emails:
        vec = embed_text(e["subject"] + " " + e["body"])
        index.add(vec.reshape(1, -1))
        conn.execute("INSERT OR REPLACE INTO mails VALUES (?, ?)", (e["path"], vec.tobytes()))
    conn.commit()
    faiss.write_index(index, "data/embeddings.faiss")

