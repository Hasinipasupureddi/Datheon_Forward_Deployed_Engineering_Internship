import json
import os
import re
import urllib.request
import urllib.error

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

ABSTENTION_PATTERNS = [
    r"i cannot answer",
    r"i can't answer",
    r"cannot be answered",
    r"could not find sufficient information",
    r"does not contain.*information",
    r"not enough information",
    r"insufficient information",
    r"unable to answer",
    r"cannot determine from the (?:provided )?context"
]


def is_abstention(answer):
    return any(
        re.search(pattern, answer.lower())
        for pattern in ABSTENTION_PATTERNS
    )


def validate_citations(answer, available_citations):
    citation_numbers = [
        int(number)
        for number in re.findall(r"\[(\d+)\]", answer)
    ]

    available_ids = {
        item["citation_id"] for item in available_citations
    }

    valid_numbers = sorted(
        set(citation_numbers).intersection(available_ids)
    )
    invalid_numbers = sorted(
        set(citation_numbers) - available_ids
    )

    for number in invalid_numbers:
        answer = re.sub(rf"\[{number}\]", "", answer)

    answer = re.sub(r" {2,}", " ", answer).strip()

    if not valid_numbers:
        return {
            "answer": (
                "I could not generate a sufficiently supported "
                "answer from the available documents."
            ),
            "citations": [],
            "abstained": True,
            "citation_validation": "failed"
        }

    return {
        "answer": answer,
        "citations": [
            item for item in available_citations
            if item["citation_id"] in valid_numbers
        ],
        "abstained": False,
        "citation_validation": (
            "passed_with_invalid_references_removed"
            if invalid_numbers else "passed"
        )
    }


def generate_grounded_answer(query, retrieved_chunks):
    if not retrieved_chunks:
        return {
            "answer": (
                "I could not find sufficient information "
                "in the available documents to answer this question."
            ),
            "citations": [],
            "abstained": True,
            "citation_validation": "not_applicable"
        }

    context_parts = []
    citations = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "Unknown")
        page = metadata.get("page_number", 0)

        citations.append({
            "citation_id": index,
            "source": source,
            "page_number": page,
            "department": metadata.get("department"),
            "access_tier": metadata.get("access_tier")
        })

        context_parts.append(
            f"[{index}]\nSource: {source}\n"
            f"Page: {page}\nContent: {chunk.get('content', '')}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are an enterprise document question-answering assistant.

Answer using ONLY the supplied document context.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. If unsupported, say:
   "I could not find sufficient information in the available documents."
4. Cite every factual claim using [1] or [2].
5. Use only citation numbers supplied in the context.
6. Do not invent sources or page numbers.
7. Be clear and concise.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{query}

ANSWER:
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.1}
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result.get("message", {}).get("content", "").strip()

        if not answer:
            return {
                "answer": (
                    "I could not generate a reliable answer "
                    "from the available documents."
                ),
                "citations": [],
                "abstained": True,
                "citation_validation": "failed"
            }

        if is_abstention(answer):
            return {
                "answer": answer,
                "citations": [],
                "abstained": True,
                "citation_validation": "not_applicable"
            }

        return validate_citations(answer, citations)

    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Ollama connection failed: {error}"
        ) from error
