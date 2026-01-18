import os
import sys
import logging
from tqdm import tqdm

# Silenciar logs HTTP verbosos
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    Document
)
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.embeddings.openai import OpenAIEmbedding

# Directorio de almacenamiento del índice
STORAGE_DIR = "storage_context"

# Configuración del servidor local - Snowflake Arctic Embed M v2.0
embed_model = OpenAIEmbedding(
    mode="similarity", 
    api_base="http://localhost:8080/v1", 
    api_key="sk-local",
    model_name="snowflake-arctic-embed-m",
    timeout=300.0,
    embed_batch_size=4,  # 4 chunks de ~400 tokens = ~1600 tokens (bajo límite de 2048)
)

Settings.llm = None
Settings.embed_model = embed_model
Settings.chunk_size = 2048
Settings.chunk_overlap = 200



# Configuración de Directorios a Indexar
SOURCE_DIRS = [
    "docs", 
    "src", 
    "ggml", 
    "common", 
    "examples", 
    "scripts"
]

# Extensiones de archivo permitidas
ALLOWED_EXTS = [".md", ".txt", ".h", ".c", ".cpp", ".hpp", ".cu", ".py", ".sh"]

def build_index():
    print(f"🔄 Iniciando Indexación de Codebase + Documentación...")
    
    all_documents = []
    
    for directory in SOURCE_DIRS:
        if not os.path.exists(directory):
            print(f"⚠️  Advertencia: No existe el directorio {directory}, saltando...")
            continue
            
        print(f"📂 Cargando archivos desde {directory}/...")
        try:
            reader = SimpleDirectoryReader(
                input_dir=directory, 
                recursive=True, 
                required_exts=ALLOWED_EXTS,
                exclude=["**/tests/*", "**/build/*", "**/node_modules/*", "**/__pycache__/*"]
            )
            docs = reader.load_data()
            print(f"   -> Encontrados {len(docs)} archivos.")
            all_documents.extend(docs)
        except Exception as e:
            print(f"   ❌ Error leyendo {directory}: {e}")

    if not all_documents:
        print("❌ Error Fatal: No se encontraron documentos para indexar.")
        return

    # Limpiar metadata reducir ruido
    print("🧹 Limpiando metadatos innecesarios...")
    for doc in all_documents:
        doc.excluded_embed_metadata_keys = ['file_size', 'creation_date', 'last_modified_date']
        doc.excluded_llm_metadata_keys = ['file_size', 'creation_date', 'last_modified_date']

    print(f"📚 Total de documentos a procesar: {len(all_documents)}")

    # Splitter: 400 tokens (Arctic GGUF tiene límite de 512, dejamos margen para metadata)
    text_splitter = TokenTextSplitter(chunk_size=400, chunk_overlap=40)
    
    print("✂️  Dividiendo en chunks (Tokens)...")
    nodes = text_splitter.get_nodes_from_documents(all_documents)
    print(f"🧩 Total de nodos (chunks) generados: {len(nodes)}")

    # Snowflake Arctic NO requiere prefijos (a diferencia de Nomic)
    print("✅ Usando Snowflake Arctic Embed (sin prefijos requeridos)")
    
    # Sanitizar nodos (remover caracteres problemáticos)
    print("🧹 Sanitizando texto de nodos...")
    for node in nodes:
        # Remover caracteres nulos y otros problemáticos
        node.text = node.text.replace('\x00', '').replace('\r', '\n')

    # Crear índice vacío
    index = VectorStoreIndex([])
    
    # Batch processing (más rápido)
    BATCH_SIZE = 30
    print(f"🚀 Insertando nodos en Vector Store (Batch={BATCH_SIZE})...")
    success_count = 0
    fail_count = 0
    
    for i in tqdm(range(0, len(nodes), BATCH_SIZE)):
        batch = nodes[i : i + BATCH_SIZE]
        try:
            index.insert_nodes(batch)
            success_count += len(batch)
        except Exception as e:
            # Fallback: intentar uno a uno
            for node in batch:
                try:
                    index.insert_nodes([node])
                    success_count += 1
                except:
                    fail_count += 1

    print(f"\n✨ Indexación finalizada.")
    print(f"✅ Chunk insertados: {success_count}")
    print(f"❌ Fallos: {fail_count}")

    if success_count > 0:
        print("💾 Guardando índice en disco...")
        index.storage_context.persist(persist_dir=STORAGE_DIR)
        print(f"🎉 ¡COMPLETADO! Índice guardado en {STORAGE_DIR}")
    else:
        print("❌ Falló la indexación completa.")

if __name__ == "__main__":
    build_index()
