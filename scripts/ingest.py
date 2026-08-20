"""
ingest.py
Loads PDF / TXT / DOCX files, chunks them, embeds them, and inserts them into Milvus.

Usage:
    python ingest.py --path ./documents --collection rag_docs
"""

import os
import argparse
import hashlib
from pathlib import Path

from pypdf import PdfReader
import docx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"   # 384-dim, fast, good quality
EMBEDDING_DIM = 384

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------
def load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    text_parts = []
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    return "\n".join(text_parts)


def load_docx(path: Path) -> str:
    document = docx.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


LOADERS = {
    ".txt": load_txt,
    ".pdf": load_pdf,
    ".docx": load_docx,
}


def load_document(path: Path) -> str:
    ext = path.suffix.lower()
    if ext not in LOADERS:
        raise ValueError(f"Unsupported file type: {ext}")
    return LOADERS[ext](path)


# ---------------------------------------------------------------------------
# Milvus setup
# ---------------------------------------------------------------------------
def get_or_create_collection(collection_name: str) -> Collection:
    if utility.has_collection(collection_name):
        return Collection(collection_name)

    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True,
                    auto_id=False, max_length=64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4000),
        FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
    ]
    schema = CollectionSchema(fields=fields, description="RAG document chunks")
    collection = Collection(name=collection_name, schema=schema)

    # HNSW index — good default for accuracy/speed tradeoff on moderate data sizes
    index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"M": 16, "efConstruction": 200},
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    return collection


def chunk_id(source_file: str, idx: int) -> str:
    raw = f"{source_file}-{idx}"
    return hashlib.md5(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Main ingestion pipeline
# ---------------------------------------------------------------------------
def ingest(path: str, collection_name: str):
    connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)

    collection = get_or_create_collection(collection_name)
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    input_path = Path(path)
    files = [input_path] if input_path.is_file() else [
        p for p in input_path.rglob("*") if p.suffix.lower() in LOADERS
    ]

    for file_path in tqdm(files, desc="Files"):
        try:
            raw_text = load_document(file_path)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            continue

        if not raw_text.strip():
            continue

        chunks = splitter.split_text(raw_text)
        embeddings = embedder.encode(chunks, normalize_embeddings=True).tolist()

        ids = [chunk_id(str(file_path), i) for i in range(len(chunks))]
        source_files = [str(file_path)] * len(chunks)
        chunk_indices = list(range(len(chunks)))

        collection.insert([ids, embeddings, chunks, source_files, chunk_indices])

    collection.flush()
    collection.load()
    print(f"Ingestion complete. Collection '{collection_name}' now has "
          f"{collection.num_entities} chunks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="File or directory to ingest")
    parser.add_argument("--collection", default="rag_docs", help="Milvus collection name")
    args = parser.parse_args()

    ingest(args.path, args.collection)
