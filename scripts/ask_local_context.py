import sys
import os

# Suppress logging warnings
import logging
logging.getLogger().setLevel(logging.ERROR)

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.openai import OpenAIEmbedding

STORAGE_DIR = "storage_context"

def get_relevant_context(query_text, top_k=3):
    if not os.path.exists(STORAGE_DIR):
        print("Error: No se encontró el índice. Ejecuta scripts/build_rag_index.py primero.")
        return []

    # Reconfigurar settings (necesario al cargar)
    embed_model = OpenAIEmbedding(
        mode="similarity", 
        api_base="http://localhost:8080/v1", 
        api_key="sk-local",
        model_name="snowflake-arctic-embed-m"
    )
    Settings.llm = None 
    Settings.embed_model = embed_model

    try:
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context)
        
        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query_text)
        return nodes
            
    except Exception as e:
        print(f"Error al consultar: {e}")
        return []

def print_results(query, nodes):
    if not nodes:
        print("No se encontró información relevante.")
        return

    print(f"--- RESULTADOS PARA: '{query}' ---\n")
    for i, node in enumerate(nodes):
        print(f"### Fragmento {i+1} (Score: {node.score:.4f})")
        print(f"Fuente: {node.metadata.get('file_path', 'N/A')}")
        print("Contenido:")
        print(node.node.get_text().strip())
        print("\n------------------------------------------------\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/ask_local_context.py 'tu pregunta'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    nodes = get_relevant_context(query)
    print_results(query, nodes)
