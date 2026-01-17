import sys
import subprocess
import os

# Asegurar que podemos importar ask_local_context desde el mismo directorio
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from ask_local_context import get_relevant_context

def get_staged_files():
    try:
        # Obtener archivos modificados en el área de preparación (staged)
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--cached'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        files = result.stdout.strip().split('\n')
        return [f for f in files if f] # Filtrar cadenas vacías
    except subprocess.CalledProcessError:
        return []

def main():
    staged_files = get_staged_files()
    if not staged_files:
        return

    print("\n🔮 RAG Hook: Analizando cambios para sugerir documentación...\n")
    
    seen_sources = set()
    found_info = False

    for file in staged_files:
        # Ignorar archivos que no sean de código o docs relevantes
        if not file.endswith(('.cpp', '.h', '.c', '.cu', '.py', '.sh', '.md')):
            continue

        print(f"  -> Buscando contexto para: {file}")
        
        # Estrategia de búsqueda: Usar el nombre del archivo y keywords básicos
        # Ej: "ggml-vulkan.cpp" -> búsqueda: "ggml vulkan implementation details"
        basename = os.path.basename(file).replace('.', ' ').replace('-', ' ')
        query = f"{basename} best practices limitations usage"
        
        nodes = get_relevant_context(query, top_k=1)
        
        for node in nodes:
            # Solo mostrar si tiene una relevancia decente (> 0.65)
            # El score en LlamaIndex suele ser 0-1 coseno similaridad
            if node.score > 0.65:
                source = node.metadata.get('file_path', 'N/A')
                
                # Evitar repetir la misma doc muchas veces
                if source in seen_sources:
                    continue
                seen_sources.add(source)
                
                print(f"\n⚠️  DOCUMENTACIÓN RELEVANTE ENCONTRADA")
                print(f"    Archivo: {file}")
                print(f"    Ver: {source} (Relevancia: {node.score:.2f})")
                print(f"    Extracto: {node.node.get_text()[:200].strip()}...\n")
                found_info = True

    if found_info:
        print("💡 Consejo: Revisa los docs sugeridos para evitar errores comunes.")
    else:
        print("✅ No se encontró documentación crítica relacionada.")
    
    print("\n------------------------------------------------\n")

if __name__ == "__main__":
    main()
