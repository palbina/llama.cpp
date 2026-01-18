# 06 - Flujo de Trabajo RAG (Git Hook Inteligente)

Este proyecto implementa un sistema de **"Documentación Proactiva"** integrado en Git. El objetivo es que el desarrollador reciba contexto relevante automáticamente justo en el momento de realizar cambios, sin tener que buscar manualmente en la documentación.

## Arquitectura

1. **Base de Conocimiento:** Archivos Markdown en `docs/` indexados vectorialmente en `storage_context/`.
2. **Motor de Búsqueda:** `start_embedding_server.sh` (llama.cpp) actuando como proveedor de embeddings (modelo `snowflake-arctic-embed-m-v2.0`).
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
  - Causa: El texto excede la ventana de contexto del modelo.
  - Solución: Ajustado `chunk_size=2048` en cliente. El servidor usa `-c 8192` y `-b 512`.
  - **Modelo:** Snowflake Arctic v2.0 (NO requiere prefijos).

- **Hook no muestra nada:**
  - Causa: O no hay archivos relevantes en stage, o la relevancia de la búsqueda no superó el umbral (0.65).
  - Verificación: Prueba con un archivo obvio (`git add examples/server/server.cpp`).

### 3. El Asistente de PR (`scripts/prepare_pr_context.py`)

Herramienta manual para generar la descripción de tus Pull Requests.

**Uso:**

```bash
source .venv/bin/activate.fish
python scripts/prepare_pr_context.py
```

**Salida:** Genera un bloque Markdown listo para copiar/pegar en GitHub, listando archivos modificados, documentación interna relacionada (links cruzados) y una checklist de cumplimiento dinámica.

### 4. Integración VS Code (Search-on-Write)

Se ha configurado `.vscode/tasks.json` para permitir consultas rápidas desde el editor.

**Cómo usar:**

1. Selecciona cualquier texto en tu código (ej: `ggml_mul_mat`).
2. Presiona `Ctrl+Shift+P` (o `F1`).
3. Escribe/Selecciona **"Tasks: Run Task"** -> **"🧠 RAG: Ask Context"**.
4. La respuesta semántica aparecerá en la terminal integrada.

También existe la tarea **"🧠 RAG: Re-index Docs"** para regenerar el índice tras editar documentación.
