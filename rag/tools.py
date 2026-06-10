import os
import re
from typing import Dict, Any, List

MD_FILE_PATH = os.path.join(os.path.dirname(__file__), "corpus", "Norme Marocaine du Béton NM 10.1.008.md")

def get_pages() -> Dict[int, str]:
    """
    Parses the markdown document and partitions it into pages using page number boundaries.
    """
    if not os.path.exists(MD_FILE_PATH):
        return {}
        
    with open(MD_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    pages = {}
    current_page = 1
    page_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for page transition pattern: line containing "NM 10.1.008-2007"
        if "NM 10.1.008-2007" in line:
            page_num_found = None
            page_num_line_offset = None
            for offset in [-3, -2, -1, 1, 2, 3]:
                check_idx = i + offset
                if 0 <= check_idx < len(lines):
                    strip_check = lines[check_idx].strip()
                    if strip_check.isdigit():
                        page_num_found = int(strip_check)
                        page_num_line_offset = offset
                        break
            
            if page_num_found is not None:
                # Save page content before transition
                pages[current_page] = "".join(page_lines)
                
                # The page number printed on the boundary indicates that page ended.
                # The content after this page boundary represents page_num + 1.
                current_page = page_num_found + 1
                page_lines = []
                
                # Skip the line with "NM 10.1.008-2007"
                i += 1
                continue
                
        page_lines.append(line)
        i += 1
        
    pages[current_page] = "".join(page_lines)
    return pages


def search_document(keyword: str) -> str:
    """
    Searches the markdown file for a keyword and returns occurrences with context (line numbers and text).
    """
    if not os.path.exists(MD_FILE_PATH):
        return "Error: Markdown standard file not found."
        
    results = []
    with open(MD_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    keyword_lower = keyword.lower()
    for idx, line in enumerate(lines):
        if keyword_lower in line.lower():
            start = max(0, idx - 2)
            end = min(len(lines), idx + 3)
            context = []
            for j in range(start, end):
                prefix = "-> " if j == idx else "   "
                context.append(f"{prefix}Ligne {j+1}: {lines[j].strip()}")
            results.append("\n".join(context))
            
            if len(results) >= 10:
                results.append("... (Plus de résultats trouvés, veuillez affiner votre recherche)")
                break
                
    if not results:
        return f"Aucun résultat trouvé pour le mot-clé : '{keyword}'"
    return "\n\n---\n\n".join(results)


def read_page(page_number: int) -> str:
    """
    Reads and returns the content of a specific page based on NM 10.1.008 page formatting.
    """
    pages = get_pages()
    if not pages:
        return "Error: Could not read pages from the markdown document."
        
    if page_number not in pages:
        # Check nearby pages if any
        available = sorted(pages.keys())
        return f"Erreur : La page {page_number} n'est pas disponible. Pages disponibles : {available}"
        
    return f"--- CONTENU DE LA PAGE {page_number} ---\n{pages[page_number].strip()}"


def read_lines(start_line: int, end_line: int) -> str:
    """
    Reads a specific range of lines from the document.
    """
    if not os.path.exists(MD_FILE_PATH):
        return "Error: Markdown standard file not found."
        
    with open(MD_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        return f"Erreur : Plage de lignes invalide. Le fichier contient {len(lines)} lignes."
        
    selected = [f"Ligne {i}: {lines[i-1].strip()}" for i in range(start_line, end_line + 1)]
    return "\n".join(selected)


tools_definitions = [
    {
        "type": "function",
        "function": {
            "name": "search_document",
            "description": "Recherche un mot-clé (ex: 'B25', 'Tableau 7', 'classe d'exposition') dans la norme marocaine du béton et renvoie les lignes correspondantes avec leur contexte.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Le mot-clé ou terme technique à rechercher."
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_page",
            "description": "Lit et renvoie l'intégralité du texte d'une page spécifique du document (de la page 1 à la page 61).",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_number": {
                        "type": "integer",
                        "description": "Le numéro de page à lire (ex: 20)."
                    }
                },
                "required": ["page_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_lines",
            "description": "Lit une plage spécifique de lignes du document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_line": {
                        "type": "integer",
                        "description": "Ligne de début (1-indexé)."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Ligne de fin (1-indexé)."
                    }
                },
                "required": ["start_line", "end_line"]
            }
        }
    }
]
