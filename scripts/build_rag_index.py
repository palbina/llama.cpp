import os
import sys

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
)
from llama_index.embeddings.openai import OpenAIEmbedding

# Configuracion: USAR SERVIDOR LOCAL DE EMBEDDINGS
# Esto apunta a ./start_embedding_server.sh (debes tenerlo corriendo)
print("Configurando cliente de embeddings local...")

embed_model = OpenAIEmbedding(
    mode="similarity", 
    api_base="http://localhost:8080/v1", 
    api_key="sk-local",  # Dummy key
    model_name="snowflake-arctic-embed-m",
    timeout=60.0,
    embed_batch_size=10,
)

# Desactivar LLM para la indexación (solo queremos crear el índice vectorial)
Settings.llm = None
Settings.embed_model = embed_model
# Reducir chunk size porque el modelo GGUF reporta max_context=512
Settings.chunk_size = 128
Settings.chunk_overlap = 20

DOCS_DIR = "docs"
STORAGE_DIR = "storage_context"

from llama_index.core.node_parser import TokenTextSplitter

def build_index():
    if not os.path.exists(DOCS_DIR):
        print(f"Error: No existe el directorio {DOCS_DIR}")
        return

    print("Cargando documentos desde docs/...")
    reader = SimpleDirectoryReader(
        input_dir=DOCS_DIR, 
        recursive=True, 
        required_exts=[".md"]
    )
    documents = reader.load_data()
    print(f"Documentos cargados: {len(documents)}")

    # FORZAR split duro para evitar el limite de 512 tokens
    text_splitter = TokenTextSplitter(chunk_size=256, chunk_overlap=20)
    
    print("Generando embeddings e índice (esto usará tu GPU)...")
    try:
        # Pasamos transformations para asegurar el split antes del embedding
        index = VectorStoreIndex.from_documents(
            documents, 
            transformations=[text_splitter],
            show_progress=True
        )
        
        print("Guardando índice en disco...")
        index.storage_context.persist(persist_dir=STORAGE_DIR)
        print(f"¡Éxito! Índice guardado en {STORAGE_DIR}")
        
    except Exception as e:
        print(f"Error generando el índice: {e}")
        print("Asegúrate de que ./start_embedding_server.sh esté corriendo en otra terminal.")

if __name__ == "__main__":
    build_index()
