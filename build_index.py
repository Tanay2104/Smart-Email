# build_index.py
import yaml
import sqlite3
import os
from src.llama import embed_text_with_llama
import faiss
import numpy as np

DOMAINS_YML = "config/domains.yml"
META_DB = "data/meta.sqlite"
INDEX_PATH = "data/embeddings.faiss"

def build_domain_index():
    with open(DOMAINS_YML) as f:
        cfg = yaml.safe_load(f)
    domains = cfg.get("domains", [])  # expect list of {"name":..., "description":...}
    if not domains:
        raise SystemExit("no domains defined in config/domains.yml")

    vectors = []
    for d in domains:
        text = d.get("description", d.get("name", ""))
        vec = embed_text_with_llama(text)
        vectors.append(np.array(vec, dtype="float32"))

    dim = vectors[0].shape[0]
    index = faiss.IndexFlatIP(dim)
    mat = np.stack(vectors, axis=0)
    faiss.normalize_L2(mat)  # optional normalization
    index.add(mat)

    os.makedirs(os.path.dirname(INDEX_PATH) or ".", exist_ok=True)
    faiss.write_index(index, INDEX_PATH)

    # write meta db with domains table (rowid corresponds to index order)
    os.makedirs(os.path.dirname(META_DB) or ".", exist_ok=True)
    conn = sqlite3.connect(META_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS domains (name TEXT, description TEXT)")
    conn.execute("DELETE FROM domains")
    for d in domains:
        conn.execute("INSERT INTO domains (name, description) VALUES (?, ?)", (d.get("name"), d.get("description", "")))
    conn.commit()
    conn.close()
    print(f"Built FAISS index at {INDEX_PATH} and meta DB at {META_DB}")

if __name__ == "__main__":
    build_domain_index()
