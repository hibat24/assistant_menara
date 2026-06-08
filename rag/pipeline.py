import os
import uuid
from typing import List
from rag.vectorstore import get_or_create_collection, add_documents_to_collection

def ingest_document(
    pdf_path: str,
    collection_name: str = "nm_10_1_008",
    tokenizer_model_id: str = "sentence-transformers/all-MiniLM-L12-v2",
    max_tokens: int = 64
) -> int:
    """
    Parses, chunks, embeds, and uploads a PDF standard document to Chroma DB.
    Returns the total number of chunks ingested.
    """
    from docling.document_converter import DocumentConverter
    from docling.chunking import HybridChunker
    from transformers import AutoTokenizer

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF document not found at: {pdf_path}")
        
    print(f"Starting ingestion of PDF: {pdf_path}")
    
    # 1. Convert document using Docling DocumentConverter
    print("Converting document with Docling...")
    converter = DocumentConverter()
    doc = converter.convert(source=pdf_path).document
    print("Document conversion completed.")
    
    # 2. Chunking with HybridChunker
    print(f"Loading tokenizer: {tokenizer_model_id}")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_model_id)
    
    print("Chunking document...")
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        merge_peers=True
    )
    
    chunks_list = list(chunker.chunk(doc))
    chunks = [c.text for c in chunks_list]
    
    num_chunks = len(chunks)
    print(f"Document split into {num_chunks} chunks.")
    
    if num_chunks == 0:
        print("No chunks generated. Ingestion aborted.")
        return 0
        
    # 3. Add chunks to Chroma DB
    metadatas = []
    ids = []
    filename = os.path.basename(pdf_path)
    
    for idx, text in enumerate(chunks):
        metadatas.append({
            "source": filename,
            "chunk_index": idx
        })
        # Generate a stable UUID5 identifier to prevent duplication on multiple runs
        chunk_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{filename}_{idx}_{text[:30]}"))
        ids.append(chunk_uuid)
        
    print("Writing chunks to Chroma DB...")
    add_documents_to_collection(
        texts=chunks,
        metadatas=metadatas,
        ids=ids,
        collection_name=collection_name
    )
    print("Ingestion completed successfully.")
    
    return num_chunks
