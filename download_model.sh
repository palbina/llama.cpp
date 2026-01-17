#!/bin/bash
MODEL_URL="https://huggingface.co/mradermacher/snowflake-arctic-embed-m-GGUF/resolve/main/snowflake-arctic-embed-m.Q4_K_M.gguf"
OUTPUT_FILE="models/snowflake-arctic-embed-m-v2.0-Q4_K_M.gguf"

# Create models directory if it doesn't exist
mkdir -p models

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Downloading model..."
    curl -L -o "$OUTPUT_FILE" "$MODEL_URL"
    
    # Check if download was successful (size check or http code check would be better, but basic check first)
    if [ ! -s "$OUTPUT_FILE" ]; then
        echo "Download failed (empty file). Trying backup URL..."
        # Backup URL hypothesis: maybe it's named differently
        # But for now, let's just warn.
        rm "$OUTPUT_FILE"
        exit 1
    fi
else
    echo "Model already exists."
fi
