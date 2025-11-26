
# src/embed.py
from .llama import embed_text_with_llama

def embed_text(text: str):
    # small pre/post processing can go here
    return embed_text_with_llama(text)
