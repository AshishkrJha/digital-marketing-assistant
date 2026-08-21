
"""
query.py
Retrieves the top-k most relevant chunks from Milvus for a user question,
then sends them as context to an LLM (Azure OpenAI shown; swap client as needed).

Usage:
    python query.py --question "What is the refund policy?" --collection rag_docs
"""

import os
import argparse
from pymilvus import connections, Collection,MilvusClient
from sentence_transformers import SentenceTransformer
from openai import AzureOpenAI  # pip install openai>=1.40
from dotenv import load_dotenv

load_dotenv()

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")



EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
TOP_K = 5

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
def retrieve_chunks(question: str, collection_name: str, top_k: int = TOP_K):
    #connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
    #collection = Collection(collection_name)
    #collection.load()
    client = MilvusClient(uri="http://localhost:19530")

    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    #query_vector = embedder.encode([question], normalize_embeddings=True).tolist()
    query_vector = embedder.encode(question).tolist()
    #search_params = {"metric_type": "COSINE", "params": {"ef": 64}}

    if isinstance(query_vector[0], list):
        search_data = query_vector
    else:
        search_data = [query_vector]



    #results = collection.search(
     #   data=query_vector,
      #  anns_field="embedding",
       # param=search_params,
        #limit=top_k,
        #output_fields=["text", "source_file", "chunk_index"],
    #)
    results = client.search(
    collection_name=collection_name,
    data=search_data,
    limit=5,
    search_params={"metric_type": "COSINE", "params": {"nprobe": 10}},
    output_fields=["text", "source_file", "chunk_index"]
      )
    
      

    #hits = []
    #for hit in results[0]:
     #   hits.append({
      #      "text": hit.entity.get("text"),
       #     "source_file": hit.entity.get("source_file"),
        #    "chunk_index": hit.entity.get("chunk_index"),
         #   "score": hit.distance,   # cosine similarity, higher = more relevant
        #})
    #return hits

    retrieved = []
    for hits in results:
        for hit in hits:
            # MilvusClient stores custom fields under 'entity'
            entity = hit.get("entity", {})
            retrieved.append({
                "score": hit.get("distance"),
                "text": entity.get("text", ""),
                "chunk_index": entity.get("chunk_index"),
                "source_file": entity.get("source_file", "")
            })

    return retrieved

# ---------------------------------------------------------------------------
# LLM call using retrieved context
# ---------------------------------------------------------------------------
def build_prompt(question: str, chunks: list) -> str:
    context_block = "\n\n---\n\n".join(
        f"[Source: {c['source_file']} | chunk {c['chunk_index']}]\n{c['text']}"
        for c in chunks
    )
    return f"""Answer the question using ONLY the context below.
If the answer is not in the context, say you don't have enough information.

Context:
{context_block}

Question: {question}

Answer:"""


def ask_llm(question: str, chunks: list) -> str:
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )

    prompt = build_prompt(question, chunks)

    response = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers "
                                           "strictly from the provided context."},
            {"role": "user", "content": prompt},
        ],
        
        max_completion_tokens=1500,
    )
    return response.choices[0].message.content



# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--collection", default="rag_docs")
    parser.add_argument("--top_k", type=int, default=TOP_K)
    args = parser.parse_args()

    retrieved = retrieve_chunks(args.question, args.collection, args.top_k)

    print("\n--- Retrieved chunks ---")
    for r in retrieved:
        print(f"[{r['score']:.4f}] {r['source_file']} (chunk {r['chunk_index']})")
        print(r["text"][:200], "...\n")

    answer = ask_llm(args.question, retrieved)
    print("\n--- LLM Answer ---")
    print(answer)
