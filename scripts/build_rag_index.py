import os
import sys
from tqdm import tqdm

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    Document
)
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.embeddings.openai import OpenAIEmbedding

# Configuración del servidor local
embed_model = OpenAIEmbedding(
    mode="similarity", 
    api_base="http://localhost:8080/v1", 
    api_key="sk-local",
    model_name="snowflake-arctic-embed-m",
    timeout=60.0,
    embed_batch_size=10,
)

Settings.llm = None
Settings.embed_model = embed_model
Settings.chunk_size = 128
Settings.chunk_overlap = 20

DOCS_DIR = "docs"
STORAGE_DIR = "storage_context"

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
    # Limpiar metadata para ahorrar tokens
    for doc in documents:
        doc.excluded_embed_metadata_keys = ['file_path', 'file_name', 'file_type', 'file_size', 'creation_date', 'last_modified_date']
        doc.excluded_llm_metadata_keys = ['file_path', 'file_name', 'file_type', 'file_size', 'creation_date', 'last_modified_date']

    print(f"Documentos brutos cargados: {len(documents)}")

    # Splitter seguro
    text_splitter = TokenTextSplitter(chunk_size=150, chunk_overlap=15)
    
    print("Pre-procesando nodos (splitting)...")
    nodes = text_splitter.get_nodes_from_documents(documents)
    print(f"Total de nodos (chunks) a procesar: {len(nodes)}")

    # Crear índice vacío
    index = VectorStoreIndex([])
    
    print("Insertando nodos en lotes (tolerancia a fallos activada)...")
    
    # Insertar manualmente para manejar errores por lote
    BATCH_SIZE = 10
    success_count = 0
    fail_count = 0
    
    for i in tqdm(range(0, len(nodes), BATCH_SIZE)):
        batch = nodes[i : i + BATCH_SIZE]
        try:
            index.insert_nodes(batch)
            success_count += len(batch)
        except Exception as e:
            print(f"\n[WARN] Falló el lote {i}-{i+BATCH_SIZE}: {e}")
            fail_count += len(batch)
            # Opcional: intentar insertar uno a uno para salvar los válidos
            for node in batch:
                try:
                    index.insert_nodes([node])
                    success_count += 1
                    fail_count -= 1
                except:
                    pass

    print(f"\nGeneración terminada. Éxitos: {success_count}, Fallos: {fail_count}")

    if success_count > 0:
        print("Guardando índice en disco...")
        index.storage_context.persist(persist_dir=STORAGE_DIR)
        print(f"¡Éxito! Índice guardado en {STORAGE_DIR}")
    else:
        print("No se pudo generar ningún embedding válido.")

if __name__ == "__main__":
    build_index()
