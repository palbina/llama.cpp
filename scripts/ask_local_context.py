import sys
import os

# Suppress logging warnings
import logging
logging.getLogger().setLevel(logging.ERROR)

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.openai import OpenAIEmbedding

STORAGE_DIR = "storage_context"

def query_rag(query_text):
    if not os.path.exists(STORAGE_DIR):
        print("Error: No se encontró el índice. Ejecuta scripts/build_rag_index.py primero.")
        sys.exit(1)

    # Reconfigurar settings (necesario al cargar)
    embed_model = OpenAIEmbedding(
        mode="similarity", 
        api_base="http://localhost:8080/v1", 
        api_key="sk-local",
        model_name="snowflake-arctic-embed-m"
    )
    Settings.llm = None # No usamos LLM para sintetizar, solo Retriever
    Settings.embed_model = embed_model

    try:
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context)
        
        # Usamos retriever para obtener los nodos crudos
        # similarity_top_k=3 trae los 3 fragmentos más relevantes
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = retriever.retrieve(query_text)
        
        if not nodes:
            print("No se encontró información relevante.")
            return

        print(f"--- RESULTADOS PARA: '{query_text}' ---\n")
        for i, node in enumerate(nodes):
            print(f"### Fragmento {i+1} (Score: {node.score:.4f})")
            print(f"Fuente: {node.metadata.get('file_path', 'N/A')}")
            print("Contenido:")
            print(node.node.get_text().strip())
            print("\n------------------------------------------------\n")
            
    except Exception as e:
        print(f"Error al consultar: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/ask_local_context.py 'tu pregunta'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    query_rag(query)
