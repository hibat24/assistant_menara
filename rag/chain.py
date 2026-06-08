from typing import Dict, Any, List
from rag.retriever import retrieve_and_rerank
from rag.prompt import apply_chat_template
from rag.llm import get_llm_client, get_llm_model_name

def run_rag_chain(
    query: str,
    collection_name: str = "nm_10_1_008",
    index_top_k: int = 4,
    reranker_top_n: int = 2,
    groq_api_key: str = None
) -> Dict[str, Any]:
    """
    Executes the full RAG pipeline:
    1. Retrieves and reranks relevant context chunks for a query.
    2. Builds the final user prompt.
    3. Calls the Groq LLM API.
    4. Returns the response and the extracted source contexts.
    """
    # Step 1: Retrieve relevant chunks
    contexts = retrieve_and_rerank(
        query=query,
        collection_name=collection_name,
        index_top_k=index_top_k,
        reranker_top_n=reranker_top_n
    )
    
    if not contexts:
        return {
            "query": query,
            "answer": "Aucun contexte pertinent n'a été trouvé dans le document pour répondre à votre question.",
            "contexts": []
        }
        
    # Step 2: Build the prompt using our template
    prompt = apply_chat_template(contexts, query)
    
    # Step 3: Run LLM inference
    if groq_api_key:
        import os
        from openai import OpenAI
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        client = OpenAI(
            base_url=base_url,
            api_key=groq_api_key
        )
    else:
        client = get_llm_client()
    model = get_llm_model_name()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0  # Kept at 0.0 to prevent hallucination in normative answers
        )
        answer = response.choices[0].message.content
    except Exception as e:
        print(f"LLM generation error: {e}")
        answer = f"Erreur lors de la génération de la réponse par le modèle LLM : {str(e)}"
        
    return {
        "query": query,
        "answer": answer,
        "contexts": contexts
    }
