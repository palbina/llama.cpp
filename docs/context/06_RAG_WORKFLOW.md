# 06 - Flujo de Trabajo RAG (Git Hook Inteligente)

Este proyecto implementa un sistema de **"Documentación Proactiva"** integrado en Git. El objetivo es que el desarrollador reciba contexto relevante automáticamente justo en el momento de realizar cambios, sin tener que buscar manualmente en la documentación.

## Arquitectura

1. **Base de Conocimiento:** Archivos Markdown en `docs/` indexados vectorialmente en `storage_context/`.
2. **Motor de Búsqueda:** `start_embedding_server.sh` (llama.cpp) actuando como proveedor de embeddings (modelo `snowflake-arctic-embed-m`).
3. **Cliente:** Scripts Python (`llama-index`) que consultan el motor.
4. **Disparador:** Hook `pre-commit` de Git.

## Componentes

### 1. El Git Hook (`.git/hooks/pre-commit`)

Es un script bash wrapper que:

1. Verifica si existe el entorno virtual `.venv`.
2. Activa el entorno.
3. Ejecuta `scripts/rag_git_check.py`.
4. Siempre permite el commit (`exit 0`), actuando solo como consejero, no como policía.

### 2. El Analizador (`scripts/rag_git_check.py`)

Lógica de funcionamiento:

1. Obtiene la lista de archivos en *stage* (`git diff --name-only --cached`).
2. Filtra solo código fuente (`.cpp`, `.h`, `.py`, etc.).
3. Genera una **query semántica** basada en el nombre del archivo (ej: `server.cpp` -> "server implementation api").
4. Consulta al índice local.
5. Si encuentra documentación con alta relevancia (> 0.65), muestra un extracto en la terminal.

## Mantenimiento del Índice

El sistema es tan bueno como su índice. Si añades nueva documentación importante, debes regenerar el índice para que el Hook la "aprenda".

**Comando de Regeneración:**

```bash
# Requiere ./start_embedding_server.sh corriendo en otra terminal
source .venv/bin/activate.fish
python scripts/build_rag_index.py
```

## Solución de Problemas Comunes

- **Error 500/400 en Indexación:**
  - Causa: El texto excede la ventana de contexto del modelo (512 tokens).
  - Solución: `build_rag_index.py` ya está configurado con `chunk_size=100` para mitigar esto agresivamente.

- **Hook no muestra nada:**
  - Causa: O no hay archivos relevantes en stage, o la relevancia de la búsqueda no superó el umbral (0.65).
  - Verificación: Prueba con un archivo obvio (`git add examples/server/server.cpp`).
