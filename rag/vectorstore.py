import os
import chromadb
from typing import List, Dict, Any, Optional
from rag.embeddings import get_embedding_function

# Resolve path to rag/chroma_db
CHROMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db"))

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Initializes and returns a persistent Chroma client pointing to rag/chroma_db.
    """
    # Ensure directory is created
    os.makedirs(CHROMA_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PATH)

def get_or_create_collection(name: str = "nm_10_1_008"):
    """
    Retrieves or creates a Chroma collection with our custom SentenceTransformer embedding function.
    """
    client = get_chroma_client()
    embedding_func = get_embedding_function()
    
    # We use cosine similarity space for normalization (value range: cosine distance = 1 - cosine_similarity)
    return client.get_or_create_collection(
        name=name,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"}
    )

def add_documents_to_collection(
    texts: List[str],
    metadatas: List[Dict[str, Any]],
    ids: List[str],
    collection_name: str = "nm_10_1_008"
):
    """
    Inserts chunks into the Chroma collection.
    """
    collection = get_or_create_collection(collection_name)
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )

def query_collection(
    query_text: str,
    n_results: int = 4,
    collection_name: str = "nm_10_1_008"
) -> List[Dict[str, Any]]:
    """
    Queries the Chroma collection and returns a list of results containing
    the text, metadata, identifier, and distance scores.
    """
    collection = get_or_create_collection(collection_name)
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    formatted_results = []
    if results and "documents" in results and results["documents"]:
        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{} for _ in documents]
        ids = results["ids"][0]
        distances = results["distances"][0] if results.get("distances") else [0.0 for _ in documents]
        
        for doc, meta, doc_id, dist in zip(documents, metadatas, ids, distances):
            # Normalize score if needed, here we provide distance directly
            formatted_results.append({
                "document": doc,
                "metadata": meta,
                "id": doc_id,
                "distance": dist
            })
            
    return formatted_results
