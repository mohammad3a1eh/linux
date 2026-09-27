import requests

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "wikipedia_search",
        "description": "Search Wikipedia and return a short summary for a given topic. Use when the user asks what something is, who someone is, or wants background information on a topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Topic or search term to look up on Wikipedia.",
                }
            },
            "required": ["query"],
        },
    },
}

_HEADERS = {"User-Agent": "voice-assistant/1.0"}
_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
_SEARCH_URL = "https://en.wikipedia.org/w/api.php"


def _fetch_summary(title: str) -> dict | None:
    resp = requests.get(
        _SUMMARY_URL.format(requests.utils.quote(title)),
        headers=_HEADERS,
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    return resp.json()


def _search_title(query: str) -> str | None:
    resp = requests.get(
        _SEARCH_URL,
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
            "format": "json",
        },
        headers=_HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    hits = resp.json().get("query", {}).get("search", [])
    if not hits:
        return None
    return hits[0]["title"]


def execute(**kwargs) -> str:
    query = (kwargs.get("query") or "").strip()
    if not query:
        return "Error: query is required."

    try:
        data = _fetch_summary(query)
        if data is None:
            title = _search_title(query)
            if title is None:
                return f"No Wikipedia article found for '{query}'."
            data = _fetch_summary(title)
        if data is None:
            return f"No Wikipedia article found for '{query}'."
    except Exception as exc:
        return f"Wikipedia lookup failed for '{query}': {exc}"

    extract = (data.get("extract") or data.get("description") or "").strip()
    if not extract:
        return f"No Wikipedia article found for '{query}'."

    url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
    if url:
        extract += f"\nSource: {url}"
    return extract