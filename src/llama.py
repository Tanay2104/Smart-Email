# src/llama.py (Fixed Version)
import subprocess
import os
import re
import yaml

CONFIG_PATH = os.path.expanduser("~/Projects/smart-mail/config/config.yml")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    print(f"Warning: Config not found at {CONFIG_PATH}")
    return {}

# Load configuration once
cfg = load_config()
LLAMA_BIN = cfg.get("llama_bin", "~/llama.cpp/build/bin/llama-cli")
MODEL_PATH = cfg.get("llama_model", "~/Projects/smart-mail/models/instruction/mistral-7b-instruct-v0.2.Q3_K_L.gguf")
EMBED_BIN = cfg.get("embed_bin", "~/llama.cpp/build/bin/llama-embedding")
EMBED_MODEL = cfg.get("embed_model", "~/Projects/smart-mail/models/embedding/bge-small-en-v1.5-f32.gguf")

def call_llama(prompt: str, max_tokens: int = 256, temperature: float = 0.2, timeout: int = 30) -> str:
    binp = os.path.expanduser(LLAMA_BIN)
    modelp = os.path.expanduser(MODEL_PATH)
    cmd = [
        binp, "-m", modelp, "-p", prompt,
        "--temp", str(temperature), "--n_predict", str(max_tokens),
        "--repeat_penalty", "1.1"
    ]
    # Existing call_llama logic is fine, keep it as is...
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout, text=False)
        stdout_text = proc.stdout.decode("utf-8", errors="replace").strip()
        stderr_text = proc.stderr.decode("utf-8", errors="replace").strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("llama.cpp invocation timed out")
    if proc.returncode != 0:
        raise RuntimeError(f"llama.cpp failed (rc={proc.returncode}): {stderr_text}")
    return stdout_text


def embed_text_with_llama(text: str, embed_bin: str = None, embed_model: str = None) -> list:
    if embed_bin is None:
        embed_bin =  EMBED_BIN
    if embed_model is None:
        embed_model = EMBED_MODEL

    embed_bin = os.path.expanduser(embed_bin)
    embed_model = os.path.expanduser(embed_model)
    # FIX: Sanitize text to prevent multiple embeddings
    # Replace newlines with spaces so the tool sees it as one single prompt
    text = text.replace("\n", " ").replace("\r", " ")
    MAX_CHARS = 512
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    cmd = [embed_bin, "-m", embed_model, "-c", "512", "-p", text]

    try:
        # FIX: Use text=False to prevent UnicodeDecodeError crashing the script
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, check=False)
        
        if proc.returncode != 0:
            stderr_text = proc.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Binary exited with error code {proc.returncode}.\nSTDERR: {stderr_text}")

        # Decode manually with replacement to handle bad bytes
        output = proc.stdout.decode("utf-8", errors="replace")
        
        # ROBUST PARSING STRATEGY (Concatenate all output first)
        # This handles cases where the vector wraps across multiple lines
        clean_output = output.replace("\n", " ").replace("\r", " ")
        
        # Regex to find "embedding <num>: <numbers...>"
        # Looks for 'embedding', an optional ID, a colon, and then a long string of numbers
        match = re.search(r"embedding(?:\s+\d+)?:?\s+((?:-?\d+(?:\.\d+)?\s*)+)", clean_output)
        
        if match:
            vector_str = match.group(1)
            try:
                vec = [float(x) for x in vector_str.split()]
                if len(vec) > 100:
                    return vec
            except ValueError:
                pass

        # Fallback: Just find the longest sequence of numbers anywhere in the output
        numbers = []
        current_chunk = []
        for token in clean_output.split():
            # Remove brackets if present
            token = token.strip("[],")
            try:
                val = float(token)
                current_chunk.append(val)
            except ValueError:
                if len(current_chunk) > 100:
                    numbers.append(current_chunk)
                current_chunk = []
        
        if len(current_chunk) > 100:
            numbers.append(current_chunk)
            
        if numbers:
            return max(numbers, key=len)

        raise RuntimeError(f"Could not parse embedding from output. Output sample: {output[:200]}...")

    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}")
