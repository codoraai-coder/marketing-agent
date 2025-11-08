# modules/blog_agent/retriever.py

import requests

WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"
WIKI_EXTRACT = "https://en.wikipedia.org/w/api.php"

def _wiki_search(query: str, limit: int = 3) -> list[str]:
    try:
        params = {
            "action": "opensearch",
            "search": query,
            "limit": str(limit),
            "namespace": "0",
            "format": "json"
        }
        r = requests.get(WIKI_SEARCH, params=params, timeout=20)
        if r.status_code == 200:
            data = r.json()
            titles = data[1] if len(data) > 1 else []
            return titles[:limit]
    except Exception:
        pass
    return []

def _wiki_extract(title: str) -> str:
    try:
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "titles": title,
            "format": "json"
        }
        r = requests.get(WIKI_EXTRACT, params=params, timeout=20)
        if r.status_code == 200:
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            for _, page in pages.items():
                extract = page.get("extract", "")
                if extract:
                    # clamp to ~2k chars for prompts
                    return extract[:2000]
    except Exception:
        pass
    return ""

def retrieve_visual_context(topic: str, description: str, extra_hint: str = "") -> str:
    """
    Retrieve quick factual/context snippets from Wikipedia to ground visuals.
    Returns a short concatenated text.
    """
    # Search using description, fallback to topic
    titles = _wiki_search(f"{description} {extra_hint}".strip()) or _wiki_search(topic)
    snippets = []
    for t in titles[:3]:
        txt = _wiki_extract(t)
        if txt:
            snippets.append(f"[{t}]\n{txt}")
    # Concatenate and clamp
    ctx = "\n\n".join(snippets)[:3000]
    return ctx or f"No external context found for '{description}'."
