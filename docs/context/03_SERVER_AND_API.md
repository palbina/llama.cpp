# 03 - Servidor y API

## `llama-server`

Servidor HTTP ligero integrado en `llama.cpp`. Implementa una API propia y un subconjunto compatible con la API de OpenAI.

### Argumentos Clave de Inicio

- **`-m <modelo.gguf>`**: Ruta al archivo del modelo.
- **`--host <ip>` / `--port <puerto>`**: Binding de red (def: 127.0.0.1:8080).
- **`-c <n>`**: Tamaño de la ventana de contexto (ej. 8192).
- **`--embedding`**: Habilita (o fuerza) capacidades de generación de embeddings.
- **`-ngl <n>`**: Capas a GPU (GPU offloading).
- **`-b <n>`**: Logical Batch size. Crítico para RAG: debe ser igual o mayor al tamaño del chunk más grande para evitar Buffer Overflows.
- **`-ub <n>`**: Physical Batch size. Para procesamiento óptimo en batches grandes, igualar a `-b`.

### Endpoints Relevantes para el Proyecto

#### 1. Inferencia de Embeddings

- **Ruta:** `POST /embedding` o `POST /v1/embeddings` (OpenAI compatible).
- **Body:**

  ```json
  {
    "content": "Texto a vectorizar",
    "image_data": [] // Opcional
  }
  ```

- **Respuesta:** Vector de punto flotante (array de floats).

#### 2. Health & Slots

- **Ruta:** `GET /health`
- **Descripción:** Verifica si el servidor está listo. Útil para orquestadores o scripts de espera.

#### 3. Métricas (Si habiltadas)

- **Ruta:** `GET /metrics`
- **Uso:** Exposición formato Prometheus (opcional en compilación).

## Caso de Uso: Embeddings

Para este proyecto, el servidor se utiliza estrictamente como un **Proveedor de Embeddings**.

- **Configuración:** `--embedding` es mandatorio.
- **Pooling:** El servidor maneja automáticamente el pooling de la última capa oculta para generar una representación vectorial semántica.
- **Batching:** `llama.server` soporta procesamiento por lotes para inferencia paralela si el cliente envía múltiples requests o un array de inputs (dependiendo de la endpoint usada).
