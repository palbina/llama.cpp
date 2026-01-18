import sys
import os
import argparse
import logging
from typing import List

# Suppress logging warnings
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
        print(f"Error al consultar índice: {e}")
        return []

def print_results(query, nodes):
    if not nodes:
        print("No se encontró información relevante.")
        return

    print(f"--- CONTEXTO ENCONTRADO PARA: '{query}' ---\n")
    for i, node in enumerate(nodes):
        print(f"### Fragmento {i+1} (Score: {node.score:.4f})")
        print(f"Fuente: {node.metadata.get('file_path', 'N/A')}")
        print("Contenido:")
        print(node.node.get_text().strip())
        print("\n------------------------------------------------\n")

def check_chat_server():
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:8081/health", timeout=1)
        return True
    except:
        return False

def generate_answer(query, nodes):
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: Librería 'openai' no instalada. No se puede generar respuesta.")
        return

    if not check_chat_server():
        print("❌ Error: El servidor de chat (puerto 8081) no está respondiendo.")
        print("Ejecuta 'make chat-server' en otra terminal.")
        return

    client = OpenAI(base_url="http://localhost:8081/v1", api_key="sk-local")
    
    context_str = "\n\n".join([f"Fuente: {n.metadata.get('file_path', 'N/A')}\n{n.node.get_text()}" for n in nodes])
    
    print(f"--- CONTEXTO RECUPERADO ({len(nodes)} fragmentos) ---\n")
    print(context_str)
    print("\n------------------------------------------------\n")
    
    system_prompt = """Eres un asistente técnico experto en llama.cpp.
Tu objetivo es EXPLICAR la respuesta al usuario basándote en el contexto proporcionado.
NO generes JSON. NO inventes llamadas a funciones.
Responde directamente a la pregunta en formato texto (Markdown verificado).
Si el contexto menciona banderas como -b o -ub, explícalas claramente."""

    user_prompt = f"""Contexto disponible:
{context_str}

Pregunta del usuario: {query}

Respuesta (SOLO TEXTO):"""

    print("\n🤖 Generando respuesta con Llama 3.2...\n")
    try:
        stream = client.chat.completions.create(
            model="Llama-3.2-3B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True,
            temperature=0.1
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print("\n")
        
    except Exception as e:
        print(f"Error generando respuesta: {e}")

def main():
    parser = argparse.ArgumentParser(description="Busca contexto y responde preguntas sobre llama.cpp")
    parser.add_argument("query", nargs="+", help="La pregunta a realizar")
    parser.add_argument("--chat", action="store_true", help="Generar una respuesta usando LLM (requiere make chat-server)")
    parser.add_argument("--top-k", type=int, default=3, help="Número de fragmentos de contexto a recuperar")
    
    args = parser.parse_args()
    query = " ".join(args.query)
    
    nodes = get_relevant_context(query, top_k=args.top_k)
    
    if args.chat:
        if nodes:
            generate_answer(query, nodes)
        else:
            print("No hay contexto suficiente para generar una respuesta.")
    else:
        print_results(query, nodes)

if __name__ == "__main__":
    main()
