# Contexto del Proyecto: Búsqueda Semántica Local (RAG Embeddings)

## 1. Visión General

Este proyecto implementa un servidor de embeddings local de alto rendimiento y bajo consumo de recursos, diseñado específicamente para potenciar un sistema RAG (Retrieval-Augmented Generation) con capacidades superiores en idioma español. El objetivo es reemplazar soluciones subóptimas (como Nomic v1.5) por una arquitectura alineada con el hardware disponible.

## 2. Estado Actual (17/01/2026)

- **Estado:** 🟢 Operativo / En Producción Local
- **Progreso:** La infraestructura base (llama.cpp compilado con Vulkan) y el modelo optimizado están desplegados y funcionando.
- **Última Acción:** Despliegue exitoso del servidor de inferencia con aceleración de GPU Iris Xe.

## 3. Arquitectura Implementada

### 3.1 Stack Tecnológico

- **Motor de Inferencia:** `llama.cpp` (Compilación personalizada `b2ff3` o superior).
- **Backend de Aceleración:** Vulkan (para Intel Iris Xe Graphics).
- **Sistema Operativo:** CachyOS (Linux optimizado para latencia).
- **Hardware Objetivo:** ASUS Zenbook (Intel Core i7-1260P, 16GB LPDDR5).

### 3.2 Modelo de Embeddings

- **Modelo:** `snowflake-arctic-embed-m-v2.0` (GGUF).
- **Cuantización:** `Q4_K_M` (~71 MB en disco, ~190 MB en RAM/VRAM).
- **Ventajas Clave:**
  - **Ventana de Contexto:** 8192 tokens (Crucial para documentos técnicos largos).
  - **Multilingüismo:** Soporte nativo y superior para Español (Benchmark MIRACL).
  - **Eficiencia:** 100% de descarga a GPU (Offload) en hardware de 16GB.

## 4. Configuración Técnica

### 4.1 Estrategia de Compilación

Se utilizó una compilación específica para maximizar el uso de instrucciones nativas de Intel y la API Vulkan:

```bash
cmake -B build -DGGML_VULKAN=1 -DGGML_NATIVE=ON
cmake --build build --config Release
```

### 4.2 Parámetros de Ejecución

El servidor se inicia con el script `start_embedding_server.sh` que aplica:

- `-ngl 99`: Fuerza la descarga de **todas** las capas a la GPU.
- `-c 8192`: Habilita el contexto completo del modelo.
- `-b 512`: Batch size optimizado para evitar saturación térmica de la Iris Xe.
- `--embedding`: Activa el modo exclusivo de embeddings (endpoint `/embeddings`).

## 5. Scripts y Herramientas

Ubicación: `/home/peter/DEV/llama.cpp/`

| Archivo | Propósito |
| :--- | :--- |
| `start_embedding_server.sh` | Lanza el servidor en puerto 8080. **Script principal de uso.** |
| `download_model.sh` | Descarga/Actualiza el modelo GGUF desde HuggingFace. |
| `find_model.py` | Utilidad Python para buscar modelos GGUF compatibles en HF. |
| `Optimización de Embeddings...md` | Informe técnico base que justifica la arquitectura. |

## 6. Próximos Pasos Pendientes

1. **Integración:** Conectar este endpoint (localhost:8080/v1/embeddings) con la base de datos vectorial (ej. ChromaDB, Qdrant) o la aplicación RAG.
2. **Pruebas de Carga:** Verificar latencia bajo estrés de ingesta de documentos.
3. **Evaluación de Calidad:** Comparar resultados de recuperación "banco" (entidad) vs "banco" (silla) en español.
