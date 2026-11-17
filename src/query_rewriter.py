
import re

TERM_EXPANSIONS = {
    "computer network": "computer networking data communication connected devices",
    "network": "networking data communication connected devices",
    "dbms": "database management system data storage",
    "database": "database management system data storage",
    "artificial intelligence": "artificial intelligence AI intelligent systems",
    "machine learning": "machine learning ML predictive models",
    "cpu": "central processing unit processor",
    "ram": "random access memory computer memory",
    "http": "hypertext transfer protocol web communication",
    "ip address": "internet protocol network address",
}


def rewrite_query(query):
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    rewritten = query.lower().strip()
    rewritten = re.sub(r"[^\w\s]", " ", rewritten)
    rewritten = re.sub(r"\s+", " ", rewritten).strip()

    # Remove conversational openings
    rewritten = re.sub(
        r"^(can you|could you|would you)\s+", "", rewritten
    )

    # Remove instruction words
    rewritten = re.sub(
        r"^(please\s+)?(explain|describe|define)\s+", "", rewritten
    )
    rewritten = re.sub(
        r"^tell me about\s+", "", rewritten
    )

    # Remove question openings and optional articles
    rewritten = re.sub(
        r"^(what|who|how|why|where|when)\s+"
        r"(?:(is|are|was|were|does|do|did)\s+)?"
        r"(?:(a|an|the)\s+)?",
        "",
        rewritten
    )

    # Remove trailing question words
    rewritten = re.sub(
        r"\s+(is|are|was|were|please)$", "", rewritten
    )

    rewritten = re.sub(r"\s+", " ", rewritten).strip()

    # Expand only the first matching technical term
    for term in sorted(TERM_EXPANSIONS, key=len, reverse=True):
        pattern = rf"\b{re.escape(term)}\b"

        if re.search(pattern, rewritten):
            rewritten = re.sub(
                pattern,
                TERM_EXPANSIONS[term],
                rewritten,
                count=1
            )
            break

    return re.sub(r"\s+", " ", rewritten).strip()
