#!/bin/bash
# Script to launch the embedding server with optimized settings for Intel i7-1260P

./build/bin/llama-server \
  -m models/snowflake-arctic-embed-m-v2.0-Q4_K_M.gguf \
  -c 8192 \
  -ngl 99 \
  --embedding \
  --port 8080 \
  -b 512
