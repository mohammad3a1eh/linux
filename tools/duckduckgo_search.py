from typing import Optional

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "duckduckgo_search",
        "description": "Search the web using DuckDuckGo and return the top 3 results (titles, URLs, snippets). Use when the user asks for current events, web info, or live queries.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query.",
                }
            },
            "required": ["query"],
        },
    },
}


def execute(**kwargs) -> str:
    query = (kwargs.get("query") or "").strip()
    if not query:
        return "Error: query is required."
    results = []
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, safesearch="moderate", max_results=3))
    except Exception as exc:
        return f"DuckDuckGo search failed for '{query}': {exc}"

    if not results:
        return f"No results found for '{query}'."

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "").strip()
        url = r.get("href") or r.get("url") or ""
        body = (r.get("body") or r.get("snippet") or "").strip()
        snippet = f"{i}. {title}"
        if url:
            snippet += f"\n   URL: {url}"
        if body:
            snippet += f"\n   {body}"
        lines.append(snippet)
    return "\n".join(lines)