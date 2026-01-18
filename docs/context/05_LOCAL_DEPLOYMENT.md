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
- **Formato:** GGUF (`Q4_K_M`)
- **Cuantización:** `Q4_K_M` (~74 MB)
- **Arquitectura:** XLM-RoBERTa (GTE base)
- **Contexto Máximo:** 512 tokens (límite del modelo GGUF)
- **Justificación:**
  - Optimizado para español (MIRACL benchmark)
  - ~1.5-2x más rápido que Nomic en Iris Xe
  - Soporte Matryoshka Embeddings
- **Prefijos:** ❌ NO requeridos (a diferencia de Nomic)

## Scripts de Operación (`/home/peter/DEV/llama.cpp/`)

### A. `start_embedding_server.sh`

Script maestro para levantar el servicio.

```bash
./build/bin/llama-server \
  -m models/snowflake-arctic-embed-m-v2.0-Q4_K_M.gguf \
  -c 8192 \     # Contexto del servidor
  -ngl 99 \     # Full GPU Offloading (Vulkan)
  --embedding \ # Modo embedding
  --port 8080 \ # Puerto estándar
  -b 2048 \     # Logical batch size
  -ub 2048      # Physical batch size (crítico para chunks grandes)
```

### B. Scripts RAG Clientes

- `build_rag_index.py`: Indexador.
  - **Estrategia:** `chunk_size=400` tokens (margen bajo límite de 512).
  - **Modelo:** Snowflake Arctic (sin prefijos requeridos).
  - **Batching:** `embed_batch_size=4` (Cliente) y `BATCH_SIZE=30` (Inserción).
- `ask_local_context.py`: Buscador semántico CLI.

## Integración RAG

Este servidor expone una API compatible con OpenAI en `http://localhost:8080/v1/embeddings`.
Cualquier cliente RAG (LangChain, LlamaIndex, scripts custom) debe configurarse con:

- **Base URL:** `http://localhost:8080/v1`
- **API Key:** (Cualquier string, ej. "sk-local")
- **Modelo:** `snowflake-arctic-embed-m`
- **Prefijos:** ❌ NO requeridos
- **Embed Batch Size:** Recomendado <= 4 para evitar exceder límite de tokens.

## Estadísticas de Indexación

- **Total Chunks:** ~19,000
- **Tasa de Éxito:** ~95%
- **Fallos:** ~5% (chunks que exceden 512 tokens con metadata)

## Comparativa de Rendimiento

| Métrica                | Nomic v1.5 (Anterior) | Arctic M v2.0 (Actual) |
|:-----------------------|:---------------------:|:----------------------:|
| Tamaño (Q4_K_M)        | ~84 MB                | ~74 MB                 |
| Arquitectura           | BERT + RoPE + SwiGLU  | XLM-RoBERTa (GTE)      |
| Contexto Máximo        | 8192 tokens           | 512 tokens             |
| Velocidad              | Base (1x)             | ~1.5-2x más rápido     |
| Rendimiento en Español | Medio/Bajo            | Muy Alto (MIRACL)      |
| Prefijos Requeridos    | Sí                    | No                     |
