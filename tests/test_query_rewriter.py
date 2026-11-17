import pytest
from src.query_rewriter import rewrite_query


@pytest.mark.parametrize("query, expected", [
    (
        "Can you explain what a computer network is?",
        "computer networking data communication connected devices"
    ),
    (
        "What is DBMS?",
        "database management system data storage"
    ),
    (
        "Tell me about database",
        "database management system data storage"
    ),
    (
        "Explain machine learning",
        "machine learning ML predictive models"
    ),
    (
        "What is artificial intelligence?",
        "artificial intelligence AI intelligent systems"
    ),
])
def test_query_rewriting(query, expected):
    assert rewrite_query(query) == expected


def test_empty_query():
    with pytest.raises(ValueError):
        rewrite_query("")


def test_whitespace_query():
    with pytest.raises(ValueError):
        rewrite_query("   ")
