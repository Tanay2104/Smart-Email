# src/faiss_helper.py
import faiss
import numpy as np
import sqlite3
import os

INDEX_PATH = os.path.expanduser(os.getenv("SMARTMAIL_FAISS", "~/projects/smart-mail/data/embeddings.faiss"))
META_DB = os.path.expanduser(os.getenv("SMARTMAIL_META_DB", "~/projects/smart-mail/data/meta.sqlite"))

class FaissHelper:
    def __init__(self):
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(f"FAISS index missing at {INDEX_PATH}")
        self.index = faiss.read_index(INDEX_PATH)
        if not os.path.exists(META_DB):
            raise FileNotFoundError(f"meta DB missing at {META_DB}")
        self.conn = sqlite3.connect(META_DB)

    def query(self, vec, k=3):
        arr = np.array(vec, dtype="float32").reshape(1, -1)
        if arr.shape[1] != self.index.d:
            raise ValueError(
                f"Dimension Error! \n"
                f"The FAISS index expects dimension: {self.index.d}\n"
                f"But the embedding model returned: {arr.shape[1]}\n"
                f"Fix: Delete 'data/embeddings.faiss' and rebuild the index, "
                f"or check your LLAMA_EMBED_MODEL."
            )
        D, I = self.index.search(arr, k)
        rows = []
        for idx, dist in zip(I[0], D[0]):
            if idx < 0:
                continue
            # rowid storage assumed to be 1-based
            cur = self.conn.execute("SELECT name, description FROM domains WHERE rowid = ?", (int(idx) + 1,))
            r = cur.fetchone()
            if r:
                rows.append({"name": r[0], "description": r[1], "score": float(dist)})
        return rows
