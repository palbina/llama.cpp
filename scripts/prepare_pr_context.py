import sys
import subprocess
import os

# Importar la lógica de búsqueda existente
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from ask_local_context import get_relevant_context

def get_changed_files(target_branch="master"):
    try:
        # Obtener archivos modificados entre la rama actual y master
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{target_branch}...HEAD'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Si falla (ej: sin commits aun), intentar diff de stage
        if result.returncode != 0 or not result.stdout:
            # Fallback 1: Staged changes
            result = subprocess.run(
                ['git', 'diff', '--name-only', '--cached'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        if result.returncode == 0 and not result.stdout:
             # Fallback 2: Unstaged changes (working directory)
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
        files = result.stdout.strip().split('\n')
        return [f for f in files if f]
    except Exception as e:
        print(f"Error git: {e}")
        return []

def generate_pr_report():
    files = get_changed_files()
    if not files:
        print("No se detectaron cambios respecto a master/main.")
        return

    print("🤖 Analizando cambios y generando plantilla de PR...\n")
    
    context_map = {}
    
    # 1. Buscar contexto para cada archivo
    for file in files:
        if not file.endswith(('.cpp', '.h', '.py', '.sh', '.md', '.txt', '.cmake')):
            continue
            
        query = f"{os.path.basename(file)} implementation details usage"
        nodes = get_relevant_context(query, top_k=1)
        
        for node in nodes:
            if node.score > 0.65:
                doc_path = node.metadata.get('file_path', 'N/A')
                # Agrupar por documento encontrado
                if doc_path not in context_map:
                    context_map[doc_path] = []
                context_map[doc_path].append(file)

    # 2. Generar Salida Markdown para copiar y pegar
    print("-" * 60)
    print("📋 COPIA Y PEGA ESTO EN TU PULL REQUEST")
    print("-" * 60)
    print("\n## 🛠️ Summary of Changes")
    print("\n*(Auto-generated list of impacted files)*")
    for f in files:
        print(f"- `{f}`")

    print("\n## 📚 Relevant Internal Documentation")
    print("Reviewers are encouraged to check these docs for context:")
    
    if context_map:
        for doc, related_files in context_map.items():
            rel_path = os.path.relpath(doc, os.getcwd())
            print(f"- **[{rel_path}]({rel_path})**")
            print(f"  - *Relevant for:* {', '.join([os.path.basename(f) for f in related_files])}")
            # Mostrar una pequeña cita si es posible (primeros 100 chars del nodo)
            # (Aquí requeriría guardar el nodo en el map, simplificamos por ahora)
    else:
        print("- *No specific internal documentation matched these changes.*")

    print("\n## ✅ Compliance Checklist")
    print("- [ ] Used `clang-format` on C++ files?")
    if any(f.endswith('.py') for f in files):
        print("- [ ] Checked Python style (PEP8)?")
    if any('CMakeLists' in f for f in files):
        print("- [ ] Verified build configuration (Vulkan/Base)?")
    
    print("\n" + "-" * 60)

if __name__ == "__main__":
    generate_pr_report()
