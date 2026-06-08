from typing import List

def apply_chat_template(contexts: List[str], query: str) -> str:
    """
    Constructs the prompt by combining the list of contexts and the user's question,
    forcing the LLM to restrict answers strictly to the provided context.
    """
    context_str = "\n\n".join([f"- {c}" for c in contexts])
    
    prompt = f"""Repondez a la question en utilisant UNIQUEMENT le contexte ci-dessous extrait de la norme marocaine NM 10.1.008.

Contexte:
{context_str}

Question:
{query}

Si la reponse ne se trouve pas dans le contexte, dites que vous ne savez pas."""
    return prompt
