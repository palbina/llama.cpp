# 04 - Herramientas y Scripts Python

El ecosistema `llama.cpp` incluye scripts vitales para preparar modelos.

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

## Scripts del Proyecto Actual

Scripts personalizados creados para el despliegue local (ver `05_LOCAL_DEPLOYMENT.md`):

- `download_model.sh`: Automatización de descarga con `curl`.
- `find_model.py`: Búsqueda en HuggingFace Hub usando API Python.
