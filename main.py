import os
import glob
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from rag.chain import run_rag_chain
from rag.pipeline import ingest_document
from rag.vectorstore import get_or_create_collection, CHROMA_PATH, get_chroma_client
from rag.llm import get_llm_model_name

app = FastAPI(
    title="Moroccan Concrete Standard NM 10.1.008 RAG Backend API",
    description="FastAPI service serving QA over Moroccan concrete specifications and standards.",
    version="1.0.0"
)

# Enable CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files folder for HTML/CSS/JS frontend
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Pydantic Schemas
class QueryRequest(BaseModel):
    query: str = Field(
        ..., 
        description="The query/question regarding NM 10.1.008 standard.", 
        json_schema_extra={"example": "Quelle est la resistance caracteristique minimale sur cylindres pour la classe B25 ?"}
    )
    index_top_k: Optional[int] = Field(4, description="Number of database contexts to retrieve.")
    reranker_top_n: Optional[int] = Field(2, description="Number of contexts to pass to the LLM after reranking.")
    groq_api_key: Optional[str] = Field(None, description="Optional Groq API key to use dynamically for LLM generation.")

class QueryResponse(BaseModel):
    query: str
    answer: str
    contexts: List[str]

class IngestResponse(BaseModel):
    status: str
    message: str
    ingested_files: List[str]
    total_chunks: int

class StatusResponse(BaseModel):
    status: str
    chroma_db_path: str
    collection_name: str
    collection_size: int
    llm_model: str
    api_key_configured: bool

@app.get("/", response_class=HTMLResponse, tags=["General"])
async def root():
    """
    Serves the HTML user interface at the API root.
    """
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    raise HTTPException(status_code=404, detail="index.html not found in static folder.")

@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query_rag(request: QueryRequest):
    """
    Executes the RAG query: retrieves relevant paragraphs from NM 10.1.008,
    reranks them, builds the prompt, calls Groq LLM API, and returns the response.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    try:
        result = run_rag_chain(
            query=request.query,
            index_top_k=request.index_top_k,
            reranker_top_n=request.reranker_top_n,
            groq_api_key=request.groq_api_key
        )
        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            contexts=result["contexts"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running RAG query: {str(e)}")

@app.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_corpus():
    """
    Scans the 'rag/corpus' directory and ingests all PDF documents into Chroma DB.
    """
    corpus_dir = os.path.join(os.path.dirname(__file__), "rag", "corpus")
    if not os.path.exists(corpus_dir):
        os.makedirs(corpus_dir, exist_ok=True)
        return IngestResponse(
            status="no_files",
            message=f"Created corpus directory at '{corpus_dir}'. Please drop your PDF documents inside.",
            ingested_files=[],
            total_chunks=0
        )
        
    pdf_files = glob.glob(os.path.join(corpus_dir, "*.pdf"))
    if not pdf_files:
        return IngestResponse(
            status="no_files",
            message="No PDF documents found in the corpus directory.",
            ingested_files=[],
            total_chunks=0
        )
        
    ingested_files = []
    total_chunks = 0
    errors = []
    
    for pdf_path in pdf_files:
        try:
            chunks = ingest_document(pdf_path)
            ingested_files.append(os.path.basename(pdf_path))
            total_chunks += chunks
        except Exception as e:
            errors.append(f"{os.path.basename(pdf_path)}: {str(e)}")
            
    if errors:
        error_msg = "; ".join(errors)
        status = "partial_success" if ingested_files else "error"
        message = f"Ingestion completed with errors: {error_msg}"
    else:
        status = "success"
        message = f"Successfully ingested {len(ingested_files)} file(s)."
        
    return IngestResponse(
        status=status,
        message=message,
        ingested_files=ingested_files,
        total_chunks=total_chunks
    )

@app.get("/status", response_model=StatusResponse, tags=["General"])
async def get_status():
    """
    Returns API status, database location, number of indexed chunks, and active configurations.
    """
    api_key = os.getenv("GROQ_API_KEY")
    api_key_configured = bool(api_key and api_key != "your_groq_api_key_here")
    
    try:
        client = get_chroma_client()
        try:
            collection = client.get_collection("nm_10_1_008")
            collection_size = collection.count()
        except Exception:
            # Collection does not exist yet
            collection_size = 0
    except Exception as e:
        print(f"Error accessing Chroma database: {e}")
        collection_size = 0
        
    return StatusResponse(
        status="online",
        chroma_db_path=CHROMA_PATH,
        collection_name="nm_10_1_008",
        collection_size=collection_size,
        llm_model=get_llm_model_name(),
        api_key_configured=api_key_configured
    )

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print(f"Starting API server at http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
