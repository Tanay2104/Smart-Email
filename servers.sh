#!/bin/bash
# TODO: Right now GPU offloading slows down the tokens per second, irrespective of partial or full overloading.
trap "kill 0" EXIT

# Load Intel environment
source /opt/intel/oneapi/setvars.sh >/dev/null

echo "--- Starting Qwen (Instruction) on Port 8080 ---"
~/llama.cpp/build/bin/llama-server \
  -m ~/Projects/smart-mail/models/instruction/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  -c 8192 \
  -np 1 \
  --no-mmap \
  --port 8080 \
  --n-gpu-layers 0 &

echo "--- Starting BGE (Embedding) on Port 8081 ---"
~/llama.cpp/build/bin/llama-server \
  -m ~/Projects/smart-mail/models/embedding/bge-small-en-v1.5-f32.gguf \
  --embedding \
  -c 4096 \
  -b 2048 \
  -np 1 \
  --port 8081 \
  --n-gpu-layers 0 &

# Wait here so the script doesn't exit immediately
echo "Servers running... Press Ctrl+C to stop."
wait
