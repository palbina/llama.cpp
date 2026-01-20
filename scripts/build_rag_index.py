import os
import sys
import hashlib
import uuid
import logging
import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Any
from tqdm.asyncio import tqdm
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, ScalarQuantization, ScalarQuantizationConfig, ScalarType
from llama_index.core.node_parser import TokenTextSplitter, MarkdownNodeParser
from llama_index.core.schema import Document

# --- SILENCIAR LOGS HTTP RUIDOSOS ---
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("qdrant_client").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# --- CONFIGURACIÓN DE RENDIMIENTO ---
# Ajustado para CPU ONLY (Intel i7-1260P - 12 Cores / 8 Threads dedicados)
BATCH_SIZE = 4         # Batch mediano para CPU (Safe mode)
CONCURRENCY = 8        # Saturar los threads del server
QDRANT_BATCH = 100     # Puntos por upsert

# --- SPLITTERS PERSONALIZADOS (SIN DEPENDENCIAS) ---
class RegexCodeSplitter:
    """Cortador de código basado en Regex para evitar dependencia de tree-sitter"""
    def __init__(self, patterns: List[str]):
        self.patterns = [re.compile(p, re.MULTILINE) for p in patterns]
        
    def split_text(self, text: str) -> List[str]:
        # Si el archivo es pequeño, devolverlo entero
        if len(text) < 1500: return [text]
        
        chunks = []
        last_pos = 0
        
        # Unir todos los patrones
        combined_pattern = re.compile('|'.join([p.pattern for p in self.patterns]), re.MULTILINE)
        
        matches = list(combined_pattern.finditer(text))
        if not matches:
            # Fallback a chunks fijos si no hay estructura clara
            return [text[i:i+1500] for i in range(0, len(text), 1500)]
            
        for i, match in enumerate(matches):
            start = match.start()
            # Tomar desde el final del anterior hasta este inicio
            if start > last_pos:
                chunk = text[last_pos:start].strip()
                if chunk: chunks.append(chunk)
            
            # Determinar fin del bloque (heurística simple: hasta el siguiente match o fin)
            end = matches[i+1].start() if i + 1 < len(matches) else len(text)
            
            # El bloque actual incluye la definición
            block = text[start:end].strip()
            # Si el bloque es gigante, trocearlo
            if len(block) > 2000:
                subchunks = [block[j:j+1500] for j in range(0, len(block), 1500)]
                chunks.extend(subchunks)
            else:
                chunks.append(block)
                
            last_pos = end
            
        return chunks

def get_splitter_for_file(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    
    # Python
    if ext == ".py":
        return RegexCodeSplitter([r"^class\s+\w+", r"^def\s+\w+"])
    
    # JS/TS
    elif ext in [".ts", ".tsx", ".js", ".jsx"]:
        return RegexCodeSplitter([
            r"^export\s+class\s+\w+", r"^class\s+\w+", 
            r"^export\s+function\s+\w+", r"^function\s+\w+",
            r"^export\s+const\s+\w+\s*:\s*React\.FC", # Typed React FC
            r"^export\s+const\s+\w+\s*=\s*\(",        # Arrow func exported
            r"^const\s+\w+\s*=\s*\("                   # Arrow func internal
        ])

    # CSS/SCSS
    elif ext in [".css", ".scss"]:
        return RegexCodeSplitter([r"^[.#]\w+", r"^@media", r"^:root"])
        
    # Markdown
    elif ext == ".md":
        return MarkdownNodeParser()
        
    else:
        # Fallback genérico (JSON, YAML, etc)
        return TokenTextSplitter(chunk_size=512, chunk_overlap=50)

# --- CONFIGURACIÓN GENERAL ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "llama_cpp_docs"
EMBEDDING_API_BASE = "http://localhost:8080/v1"
EMBEDDING_MODEL_NAME = "nomic-embed-text-v1.5"
VECTOR_SIZE = 768

BASE_DIR = "/home/peter/DEV/llama.cpp"
PROJECT_DIRS = [
    BASE_DIR,
]

ALLOWED_EXTS = {".md", ".txt", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".css", ".scss", ".sh", ".dockerfile", "Dockerfile", ".conf", ".py"}
EXCLUDE_DIRS = {"node_modules", "dist", "build", ".git", ".next", "__pycache__", "coverage", ".venv", "venv", ".idea", ".vscode", "storage_context", "public"}
EXCLUDE_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "composer.lock", "cargo.lock"}

# --- ESTRUCTURAS ---

class ChunkContext:
    def __init__(self, text: str, file_path: str, file_hash: str, index: int):
        self.text = text
        self.file_path = file_path
        self.file_hash = file_hash
        self.index = index
        self.vector = None

# --- CORE ---

def get_file_hash_sync(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()

async def get_embeddings_async(session, texts: List[str]) -> List[List[float]]:
    prefixed_texts = [f"search_document: {t}" for t in texts]
    payload = {"input": prefixed_texts, "model": EMBEDDING_MODEL_NAME}
    
    try:
        async with session.post(f"{EMBEDDING_API_BASE}/embeddings", json=payload) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Error API Embeddings: {text}")
                return []
            data = await response.json()
            data["data"].sort(key=lambda x: x["index"])
            return [x["embedding"] for x in data["data"]]
    except Exception as e:
        logger.error(f"Excepción en request embeddings: {e}")
        return []

async def scan_and_prep_files(client: QdrantClient) -> List[ChunkContext]:
    print("🔍 Fase 1: Escaneo Inteligente (RegexCodeSplitter + CPU)...")
    
    files_to_check = []
    for p_dir in PROJECT_DIRS:
        if not os.path.exists(p_dir): continue
        for root, dirs, files in os.walk(p_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f in EXCLUDE_FILES or os.path.splitext(f)[1] not in ALLOWED_EXTS: continue
                files_to_check.append(os.path.join(root, f))
    
    chunks_buffer = []
    stats = {"skipped": 0, "queued": 0}

    loop = asyncio.get_running_loop()
    
    async def process_single_file(path):
        try:
            curr_hash = await loop.run_in_executor(None, get_file_hash_sync, path)
            
            # --- PROCESAMIENTO ---
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if not content.strip(): return

            splitter = get_splitter_for_file(path)
            file_chunks = []
            
            if isinstance(splitter, MarkdownNodeParser):
                docs = [Document(text=content)]
                nodes = splitter.get_nodes_from_documents(docs)
                file_chunks = [n.text for n in nodes]
            else:
                file_chunks = splitter.split_text(content)

            # Debug primera vez
            if file_chunks and len(file_chunks) > 0 and path.endswith(".ts") and stats["queued"] == 0:
                 preview = file_chunks[0][:80].replace('\n', ' ')
                 print(f"✨ DEBUG Sample Chunk ({path}): [{preview}...] (Length: {len(file_chunks[0])})")

            # --- LÓGICA INCREMENTAL ROBUSTA ---
            try:
                # Verificar si el archivo ya existe con el MISMO hash Y el MISMO número de chunks
                count = await loop.run_in_executor(None, lambda: client.count(
                    collection_name=COLLECTION_NAME,
                    count_filter=models.Filter(
                        must=[
                            models.FieldCondition(key="file_path", match=models.MatchValue(value=path)),
                            models.FieldCondition(key="file_hash", match=models.MatchValue(value=curr_hash))
                        ]
                    )
                ))
                
                # Solo saltar si están TODOS los chunks
                if count.count == len(file_chunks):
                    stats["skipped"] += 1
                    return

                # Si no coinciden (o es 0), borrar y re-indexar
                if count.count > 0:
                    await loop.run_in_executor(None, lambda: client.delete(
                        collection_name=COLLECTION_NAME,
                        points_selector=models.FilterSelector(
                            filter=models.Filter(
                                must=[models.FieldCondition(key="file_path", match=models.MatchValue(value=path))]
                            )
                        )
                    ))
                
            except Exception as e:
                # Si la colección no existe aún, ignorar
                pass

            for i, txt in enumerate(file_chunks):
                chunks_buffer.append(ChunkContext(txt, path, curr_hash, i))
            stats["queued"] += 1
            
        except Exception as e:
            logger.error(f"Error prep {path}: {e}")

    # I/O Bound scan
    scan_semaphore = asyncio.Semaphore(50)
    async def guarded_scan(f):
        async with scan_semaphore: await process_single_file(f)
    
    tasks = [guarded_scan(f) for f in files_to_check]
    await tqdm.gather(*tasks, desc="📂 Escaneando Cambios")
    
    # Safety Pass: Ensure no chunk exceeds limits
    final_chunks = []
    for c in chunks_buffer:
        if len(c.text) > 1500:
            # Recursively split large chunks
            subchunks = [c.text[i:i+1500] for i in range(0, len(c.text), 1500)]
            for j, sub in enumerate(subchunks):
                final_chunks.append(ChunkContext(sub, c.file_path, c.file_hash, c.index + j))
        else:
            final_chunks.append(c)
            
    print(f"📊 Estado: {stats['skipped']} sin cambios, {len(final_chunks)} chunks generados.")
    return final_chunks

async def main():
    print(f"🚀 Iniciando Indexación Incremental (Code-Aware)...")
    
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    try:
        client.get_collections()
    except Exception:
        print("❌ Error conectando a Qdrant.")
        return

    # Crear colección SOLO si no existe
    collections = client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        print(f"⚙️ Creando Colección '{COLLECTION_NAME}' (primera vez)...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            quantization_config=ScalarQuantization(scalar=ScalarQuantizationConfig(type=ScalarType.INT8, always_ram=True)),
            optimizers_config=models.OptimizersConfigDiff(memmap_threshold=20000)
        )
    else:
        print(f"✅ Colección '{COLLECTION_NAME}' detectada. Modo Incremental Activo.")

    all_chunks = await scan_and_prep_files(client)
    if not all_chunks: 
        print("🎉 Todo al día. Nada que indexar.")
        return

    # Batch Process
    semaphore = asyncio.Semaphore(CONCURRENCY)
    session_timeout = aiohttp.ClientTimeout(total=300)
    
    async with aiohttp.ClientSession(timeout=session_timeout) as session:
        # Agrupar en super-batches
        total_batches = [all_chunks[i:i + BATCH_SIZE] for i in range(0, len(all_chunks), BATCH_SIZE)]
        
        async def process_batch(batch):
            async with semaphore:
                texts = [c.text for c in batch]
                embeddings = await get_embeddings_async(session, texts)
                
                if not embeddings or len(embeddings) != len(batch):
                    return # Skip error

                points = []
                for j, ctx in enumerate(batch):
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{ctx.file_path}_{ctx.index}"))
                    payload = {
                        "file_path": ctx.file_path,
                        "file_name": os.path.basename(ctx.file_path),
                        "file_hash": ctx.file_hash,
                        "text": ctx.text, # Qdrant 'text' field = CODE BLOCK
                        "chunk_index": ctx.index,
                        "project": os.path.basename(os.path.dirname(os.path.dirname(ctx.file_path))),
                        "is_code_chunk": True 
                    }
                    points.append(models.PointStruct(id=point_id, vector=embeddings[j], payload=payload))
                
                if points:
                    await loop.run_in_executor(None, lambda: client.upsert(
                        collection_name=COLLECTION_NAME, points=points, wait=False
                    ))

        loop = asyncio.get_running_loop()
        tasks = [process_batch(b) for b in total_batches]
        print(f"⚡ Procesando {len(tasks)} Batches en CPU ({BATCH_SIZE} chunks/batch)...")
        await tqdm.gather(*tasks, desc="🔥 Embed & Upsert")

    print("✅ Indexación Completada.")

if __name__ == "__main__":
    asyncio.run(main())
