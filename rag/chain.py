import json
from typing import Dict, Any, List
from rag.tools import search_document, read_page, read_lines
from rag.llm import get_llm_client, get_llm_model_name


def run_rag_chain(
    query: str,
    collection_name: str = "nm_10_1_008",
    index_top_k: int = 4,
    reranker_top_n: int = 2,
    groq_api_key: str = None
) -> Dict[str, Any]:
    """
    Executes the Agentic Search pipeline using a robust ReAct (prompt-based) loop.
    1. Instantiates the LLM client (Groq API).
    2. Instructs the model to output JSON tool calls in its text when it needs tools.
    3. Runs an execution loop in Python to call local document tools (search, read_page, read_lines).
    4. Outputs the final answer in French once the agent gathers the facts.
    """
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
    
    # Map function names to executable Python helpers
    available_tools = {
        "search_document": search_document,
        "read_page": read_page,
        "read_lines": read_lines
    }
    
    # ReAct agent instructions
    system_prompt = (
        "Vous êtes un ingénieur expert et assistant technique pour la Norme Marocaine du Béton (NM 10.1.008).\n"
        "Vous ne connaissez pas la norme par cœur. Vous devez utiliser des outils pour rechercher et lire le document.\n\n"
        "Pour utiliser un outil, vous devez répondre UNIQUEMENT avec un objet JSON valide contenant l'action et ses arguments. "
        "Ne mettez aucun texte ou explication en dehors du JSON si vous appelez un outil. Exemple de format :\n"
        "{\n"
        "  \"action\": \"search_document\",\n"
        "  \"arguments\": {\"keyword\": \"B25\"}\n"
        "}\n\n"
        "Actions d'outils disponibles :\n"
        "- search_document(keyword: str) : Recherche des occurrences d'un mot-clé.\n"
        "- read_page(page_number: int) : Lit le contenu entier d'une page spécifique (de la page 1 à la page 61).\n"
        "- read_lines(start_line: int, end_line: int) : Lit une plage de lignes.\n\n"
        "Une fois que vous avez trouvé l'information précise dans le document et que vous êtes prêt à répondre à l'utilisateur, "
        "répondez normalement en français en décrivant l'explication et en citant les pages ou lignes concernées (ex: Page 20). "
        "Ne générez pas de JSON dans votre réponse finale."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    contexts = []
    
    # Loop up to 6 iterations to prevent infinite search loops
    for step in range(6):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0
            )
        except Exception as e:
            print(f"Error calling LLM during agent loop step {step}: {e}")
            return {
                "query": query,
                "answer": f"Erreur lors de la génération de la réponse par le modèle LLM : {str(e)}",
                "contexts": contexts
            }
            
        response_text = response.choices[0].message.content.strip()
        
        # Parse action if output is formatted as JSON
        is_tool_call = False
        action, args = None, None
        
        # Clean potential markdown block wrappers
        clean_text = response_text
        if clean_text.startswith("```"):
            lines = clean_text.split("\n")
            json_lines = [l for l in lines if not l.strip().startswith("```")]
            clean_text = "\n".join(json_lines).strip()
            
        if clean_text.startswith("{") and clean_text.endswith("}"):
            try:
                data = json.loads(clean_text)
                if "action" in data and "arguments" in data:
                    is_tool_call = True
                    action = data["action"]
                    args = data["arguments"]
            except Exception:
                pass
                
        if is_tool_call:
            print(f"[Agent Step {step+1}] Appel de '{action}' avec: {args}")
            if action in available_tools:
                try:
                    tool_output = available_tools[action](**args)
                except Exception as exc:
                    tool_output = f"Erreur lors de l'exécution de l'outil : {exc}"
            else:
                tool_output = f"Erreur : L'outil '{action}' n'est pas disponible."
                
            contexts.append(tool_output)
            
            # Record assistant call and user response (tool feedback) in context log
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"Résultat de l'outil:\n{tool_output}"})
        else:
            # Direct text response represents the final answer
            return {
                "query": query,
                "answer": response_text,
                "contexts": contexts
            }
            
    return {
        "query": query,
        "answer": "Désolé, l'agent a pris trop de temps de recherche pour trouver la réponse.",
        "contexts": contexts
    }


