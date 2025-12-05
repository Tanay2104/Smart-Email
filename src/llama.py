import requests
import json
import os

# Configuration
CHAT_API_URL = "http://localhost:8080/completion"
EMBED_API_URL = "http://localhost:8081/embedding"


def call_llama(
    prompt: str, max_tokens: int = 256, temperature: float = 0.2, timeout: int = 120
) -> str:
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": temperature,
        "repeat_penalty": 1.1,
        "stop": [],
    }
    try:
        response = requests.post(
            CHAT_API_URL, headers=headers, json=data, timeout=timeout
        )
        response.raise_for_status()
        return response.json().get("content", "").strip()
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return ""


def embed_text_with_llama(
    text: str, embed_bin: str = None, embed_model: str = None
) -> list:
    # 1. Clean newlines
    text = text.replace("\n", " ").replace("\r", " ")

    # 2. Truncate to prevent crashing the BGE model (Limit ~600 chars)
    if len(text) > 600:
        text = text[:600]

    headers = {"Content-Type": "application/json"}
    data = {"content": text}

    try:
        response = requests.post(EMBED_API_URL, headers=headers, json=data, timeout=30)

        if response.status_code != 200:
            print(f"Embedding API Error {response.status_code}: {response.text}")
            return [0.0] * 384

        result = response.json()

        # --- FIX STARTS HERE ---
        embedding = []

        # Case A: Server returned a List (The source of your error)
        if isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], dict):
                embedding = result[0].get("embedding", [])
            elif len(result) > 0 and isinstance(result[0], float):
                # Rare case: returned raw list of floats
                embedding = result

        # Case B: Server returned a Dict (Standard behavior)
        elif isinstance(result, dict):
            # Check for OpenAI format {"data": [{"embedding": ...}]}
            if "data" in result and isinstance(result["data"], list):
                embedding = result["data"][0].get("embedding", [])
            # Check for Native format {"embedding": [...]}
            else:
                embedding = result.get("embedding", [])

        # Final check: Flatten if nested (e.g. [[0.1, 0.2]])
        if embedding and isinstance(embedding[0], list):
            embedding = embedding[0]

        # Return zero vector if empty
        if not embedding:
            return [0.0] * 384

        return embedding
        # --- FIX ENDS HERE ---

    except Exception as e:
        print(f"Error calling Embedding Server: {e}")
        return [0.0] * 384
