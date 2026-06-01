import requests

def search_wikipedia(query: str) -> str:
    """Search Wikipedia for a given topic. Input: topic to search (string). Returns a brief summary."""
    try:
        # Using Wikipedia's open API
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": query.strip(),
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "redirects": 1
        }
        headers = {
            "User-Agent": "ChatbotVsReActAgent/1.0 (https://github.com/example/repo; user@example.com) requests/2.x"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_info in pages.items():
            if page_id == "-1":
                return f"No Wikipedia article found for '{query}'."
            extract = page_info.get("extract", "")
            # Return first 300 characters to save tokens
            if len(extract) > 300:
                return extract[:300] + "..."
            return extract if extract else f"Found page for '{query}' but it has no text."
            
    except Exception as e:
        return f"Error connecting to Wikipedia: {str(e)}"
