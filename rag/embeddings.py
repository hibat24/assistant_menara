import os
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

class MiniLMEmbeddingFunction(EmbeddingFunction):
    """
    Custom Chroma EmbeddingFunction that utilizes SentenceTransformer
    to generate embeddings for document chunks and queries.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Embedding model loaded successfully.")

    def __call__(self, input: Documents) -> Embeddings:
        # Generate embeddings and convert numpy array to list of floats for Chroma
        embeddings = self.model.encode(input)
        return embeddings.tolist()

_embedding_function = None

def get_embedding_function() -> MiniLMEmbeddingFunction:
    """
    Singleton getter for the custom Chroma embedding function.
    """
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = MiniLMEmbeddingFunction()
    return _embedding_function
