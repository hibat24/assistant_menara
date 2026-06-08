import os
from openai import OpenAI
from dotenv import load_dotenv

# Load configuration variables from .env
load_dotenv()

_llm_client = None

def get_llm_client() -> OpenAI:
    """
    Initializes and returns the OpenAI client configured for the Groq endpoint.
    """
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        
        # We handle missing API keys gracefully at initialization time
        if not api_key:
            print("[Warning] GROQ_API_KEY environment variable is not defined.")
            
        _llm_client = OpenAI(
            base_url=base_url,
            api_key=api_key or "DUMMY_KEY"
        )
    return _llm_client

def get_llm_model_name() -> str:
    """
    Returns the configured model identifier, defaulting to llama-3.3-70b-versatile.
    """
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
