# 05 - Despliegue Local (Búsqueda Semántica)

## Estado del Proyecto

Implementación de un servidor de embeddings optimizado para **Español** en hardware **Intel Alder Lake**.

## Configuración Específica

### 1. Hardware

- **CPU:** Intel Core i7-1260P (P-cores + E-cores).
- **GPU:** Intel Iris Xe Graphics.
- **RAM:** 16GB LPDDR5.
- **OS:** Linux CachyOS.

### 2. Stack de Software

- **Compilación:** `cmake -DGGML_VULKAN=1 -DGGML_NATIVE=ON`.
- **Backend:** Vulkan (Offloading crítico para rendimiento).

### 3. Modelo Seleccionado

- **Nombre:** `snowflake-arctic-embed-m-v2.0`
- **Formato:** GGUF
- **Cuantización:** `Q4_K_M` (~71 MB)
- **Justificación:** Mejor balance tamaño/semántica-español. Soporta ventana de 8192 tokens.

## Scripts de Operación (`/home/peter/DEV/llama.cpp/`)

### A. `start_embedding_server.sh`

Script maestro para levantar el servicio.

```bash
./build/bin/llama-server \
  -m models/snowflake-arctic-embed-m-v2.0-Q4_K_M.gguf \
  -c 8192 \     # Contexto completo
  -ngl 99 \     # TODO a la GPU (modelo pequeño cabe en VRAM compartida)
  --embedding \ # Modo embedding
  --port 8080 \ # Puerto estándar
  -b 2048 \     # Batch size aumentado para chunks grandes
  -ub 2048      # Physical batch size igualado
```

### B. `download_model.sh`

Script de recuperación ante desastres o configuración inicial. Descarga el modelo específico desde HuggingFace.

### C. Scripts RAG Clientes

- `build_rag_index.py`: Indexador.
  - **Estrategia:** `chunk_size=200` y `TokenTextSplitter`.
  - **Optimización:** Se excluye toda metadata (`file_path`, etc.) del vector para ahorrar tokens, ya que el modelo GGUF a veces rechaza inputs >512 tokens a pesar de soportar 8192.
- `ask_local_context.py`: Buscador semántico CLI.

## Integración RAG

Este servidor expone una API compatible con OpenAI en `http://localhost:8080/v1/embeddings`.
Cualquier cliente RAG (LangChain, LlamaIndex, scripts custom) debe configurarse con:

- **Base URL:** `http://localhost:8080/v1`
- **API Key:** (Cualquiera string, ej. "sk-local")
- **Modelo:** `snowflake-arctic-embed-m` (o alias configurado).
- **Embed Batch Size:** Recomendado <= 10 para evitar saturar el queue local.
