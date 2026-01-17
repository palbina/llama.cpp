# 01 - Descripción General del Proyecto y Estructura

## Descripción

`llama.cpp` es un motor de inferencia para Modelos Grandes de Lenguaje (LLMs) escrito en C/C++ puro sin dependencias externas pesadas. Su objetivo principal es ejecutar modelos de vanguardia (como Llama 3, Mistral, etc.) en hardware de consumo (Apple Silicon, x86 con AVX2, GPUs NVIDIA/AMD/Intel) con alta eficiencia.

## Estructura de Directorios Clave

| Ruta | Descripción |
| :--- | :--- |
| **`/`** | Raíz del proyecto. Contiene `Makefile`, `CMakeLists.txt` y documentación raíz. |
| **`/src`** | Código fuente principal (`llama.cpp`, `llama.h`). Implementación del motor. |
| **`/ggml`** | Biblioteca de tensores subyacente. Maneja la computación de bajo nivel (CPU/GPU). |
| **`/examples`** | Ejemplos de uso y herramientas clave. |
| **`/examples/server`** | Código fuente del servidor HTTP (`llama-server`). |
| **`/examples/embedding`** | Ejemplo específico de generación de embeddings. |
| **`/models`** | Directorio (generalmente git-ignored) para almacenar modelos `.gguf`. |
| **`/scripts`** | Scripts de utilidad (bash, python). |
| **`/tools`** | Herramientas de desarrollo y mantenimiento. |

## Sistema de Construcción (Build)

El proyecto soporta `make` (UNIX estándar) y `cmake` (multiplataforma).

### Comandos de Construcción Comunes

- **CPU (Básico):** `cmake -B build && cmake --build build -j`
- **Vulkan (GPUs Intel/AMD):** `cmake -B build -DGGML_VULKAN=1 && cmake --build build -j`
- **CUDA (NVIDIA):** `cmake -B build -DGGML_CUDA=1 && cmake --build build -j`

## Binarios Principales Generados

Tras compilar, los ejecutables suelen estar en `build/bin/`:

- **`llama-cli` (antes `main`):** Herramienta de línea de comandos para inferencia de texto.
- **`llama-server`:** Servidor HTTP compatible con OpenAI API.
- **`llama-quantize`:** Herramienta para cuantizar modelos (f16 -> q4_k, etc.).
- **`llama-embedding`:** Herramienta CLI dedicada a embeddings.
