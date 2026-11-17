
from src.llm import (
    validate_citations,
    is_abstention
)


def sample_citations():
    return [
        {
            "citation_id": 1,
            "source": "sample.pdf",
            "page_number": 1
        },
        {
            "citation_id": 2,
            "source": "sample.pdf",
            "page_number": 3
        }
    ]


def test_valid_citation():
    result = validate_citations(
        "A network connects devices [1].",
        sample_citations()
    )

    assert result["citation_validation"] == "passed"
    assert len(result["citations"]) == 1
    assert result["citations"][0]["citation_id"] == 1


def test_invalid_citation_removed():
    result = validate_citations(
        "A network connects devices [99].",
        sample_citations()
    )

    assert result["abstained"] is True
    assert result["citations"] == []
    assert result["citation_validation"] == "failed"


def test_mixed_citations():
    result = validate_citations(
        "Networks connect devices [1] [99].",
        sample_citations()
    )

    assert result["citations"][0]["citation_id"] == 1
    assert "[99]" not in result["answer"]
    assert result["citation_validation"] == (
        "passed_with_invalid_references_removed"
    )


def test_abstention_detection():
    assert is_abstention(
        "I could not find sufficient information."
    )


def test_normal_answer_is_not_abstention():
    assert not is_abstention(
        "A computer network connects multiple devices [1]."
    )


def test_duplicate_citations():
    result = validate_citations(
        "Networks connect devices [1] [1].",
        sample_citations()
    )

    assert len(result["citations"]) == 1


def test_no_citations():
    result = validate_citations(
        "A computer network connects devices.",
        sample_citations()
    )

    assert result["abstained"] is True
    assert result["citations"] == []
