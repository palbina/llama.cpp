# 04 - Herramientas y Scripts Python

El ecosistema `llama.cpp` incluye scripts vitales para preparar modelos, y este proyecto añade herramientas específicas para RAG.

## Scripts de Conversión (`convert_hf_to_gguf.py`)

Convierte modelos desde formato HuggingFace (PyTorch/Safetensors) a GGUF.

- **Ubicación:** Raíz del proyecto.
- **Uso:**

  ```bash
  python3 convert_hf_to_gguf.py /ruta/modelo-hf/ --outfile modelo.gguf --outtype f16
  ```

- **Requisitos:** `pip install -r requirements.txt` (torch, transformers, sentencepiece).

## Herramientas de GGUF (`gguf-py`)

Paquete Python para manipular archivos GGUF.

- **Instalación:** `pip install gguf`
- **Utilidades:**
  - Leer metadatos.
  - Modificar arquitectura (ej. cambiar nombre).
  - Extraer vocabulario.

## `llama-quantize` (Binario C++)

Convierte un modelo GGUF de alta precisión (F16/F32) a versiones cuantizadas.

- **Uso:**

  ```bash
  ./llama-quantize modelo-f16.gguf modelo-q4_k_m.gguf q4_k_m
  ```

- **Flujo Típico:** HF -> `convert_hf_to_gguf` (f16) -> `llama-quantize` (q4) -> Inferencia.

## Scripts del Proyecto (RAG Local)

Scripts personalizados ubicados en `scripts/` para gestionar la base de conocimiento semántica.

| Script | Descripción | Uso Típico |
| :--- | :--- | :--- |
| `build_rag_index.py` | **Indexador Robusto.** Divide docs en nodos pequeños (150 tokens) e inserta por lotes con recuperación de errores. Excluye metadatos para optimizar contexto. | `python scripts/build_rag_index.py` |
| `ask_local_context.py` | **Buscador CLI.** Realiza consultas semánticas al índice guardado y devuelve los fragmentos más relevantes con su puntaje de similitud. | `python scripts/ask_local_context.py "pregunta"` |
| `rag_git_check.py` | **Git Hook.** Analiza archivos en *stage* y busca documentación relevante automáticamente antes de cada commit. | Ejecución automática por Git (pre-commit). |

> **Nota:** Estos scripts requieren el entorno virtual activo (`source .venv/bin/activate.fish`) y el servidor de embeddings (`./start_embedding_server.sh`) corriendo.
