from typing import List, Dict, Any
from rag.vectorstore import query_collection

# None: not initialized; False: initialization failed; Object: model instance
_reranker_model = None

def get_reranker_model():
    """
    Initializes and returns the Jina reranker model.
    Falls back to None if model fails to load (e.g. due to memory or dependencies).
    """
    global _reranker_model
    if _reranker_model is None:
        try:
            from transformers import AutoModel
            import torch
            RERANKER_MODEL_ID = 'jinaai/jina-reranker-v3'
            print(f"Loading reranker model: {RERANKER_MODEL_ID}...")
            
            # Check if CUDA is available for GPU acceleration
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Reranker device target: {device}")
            
            _reranker_model = AutoModel.from_pretrained(
                RERANKER_MODEL_ID,
                dtype="auto",
                device_map=device,
                trust_remote_code=True,
            ).eval()
            print("Reranker model loaded successfully.")
        except Exception as e:
            print(f"Error loading Jina reranker model: {e}.")
            print("Retrieval will fall back to default vector similarity scores.")
            _reranker_model = False  # Mark as failed to avoid re-attempting
            
    return _reranker_model if _reranker_model is not False else None

def retrieve_and_rerank(
    query: str,
    collection_name: str = "nm_10_1_008",
    index_top_k: int = 4,
    reranker_top_n: int = 2
) -> List[str]:
    """
    Retrieves the top_k chunks from Chroma DB and reranks them to return the top_n most relevant contexts.
    """
    # Retrieve top K documents from Chroma vector store
    db_results = query_collection(query, n_results=index_top_k, collection_name=collection_name)
    if not db_results:
        return []
        
    retrieved_texts = [r["document"] for r in db_results]
    
    # Try reranking the documents
    reranker = get_reranker_model()
    if reranker:
        try:
            print(f"Reranking {len(retrieved_texts)} contexts using Jina reranker...")
            # Note: the Jina reranker v3 model downloaded from transformers has a rerank method
            rerank_results = reranker.rerank(query, retrieved_texts, top_n=reranker_top_n)
            reranked_texts = [r["document"] for r in rerank_results]
            return reranked_texts
        except Exception as e:
            print(f"Reranking error: {e}. Falling back to default database retrieval order.")
            
    # Fallback to returning top_n from vector store distance scores directly
    return retrieved_texts[:reranker_top_n]
