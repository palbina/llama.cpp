#!/bin/bash
# Script to launch the embedding server with optimized settings for Intel i7-1260P
# Model: Snowflake Arctic Embed M v2.0 - Optimizado para español y bajo uso de recursos

./build/bin/llama-server \
  -m models/snowflake-arctic-embed-m-v2.0-Q4_K_M.gguf \
  -c 8192 \
  -ngl 99 \
  --embedding \
  --port 8080 \
  -b 2048 \
  -ub 2048
