# 02 - Conceptos Core: GGUF y Cuantización

## GGUF (GPT-Generated Unified Format)

Es el formato de archivo binario utilizado por `llama.cpp` para distribuir modelos.

- **Eficiencia:** Diseñado para mapeo de memoria rápido (mmap). Carga instantánea.
- **Contenido:** Incluye los tensores del modelo, hiperparámetros y vocabulario en un solo archivo.
- **Identificación:** Cabecera mágica `GGUF`. Versionado.

## Cuantización (Quantization)

Técnica clave para reducir el uso de memoria y aumentar la velocidad con pérdida mínima de precisión. `llama.cpp` es famoso por sus "K-quants" (K-means quantization).

### Tipos Comunes

| Tipo | Bits/Peso (aprox) | Uso Recomendado |
| :--- | :--- | :--- |
| **F16** | 16.0 | Calidad original (alta memoria). Referencia. |
| **Q8_0** | 8.0 | Casi sin pérdida. Muy rápido en CPU. |
| **Q6_K** | 6.6 | "Pérdida imperceptible". |
| **Q5_K_M** | 5.7 | Gran equilibrio. |
| **Q4_K_M** | 4.8 | **Estándar de facto.** Mejor balance calidad/tamaño. |
| **IQ4_XS** | 4.3 | Nueva técnica (I-Quants) para mayor compresión. |

## Inferencia Híbrida (Offloading)

`llama.cpp` permite dividir la carga de trabajo entre CPU y GPU.

- **Argumento:** `-ngl N` o `--n-gpu-layers N`.
- **Funcionamiento:** Mueve las primeras N capas del modelo a la VRAM.
- **Offload Total:** Si N >= total de capas, todo el modelo corre en GPU (máxima velocidad).
- **Importancia:** Vital para hardware limitado (ej. iGPUs) o para liberar RAM del sistema.
