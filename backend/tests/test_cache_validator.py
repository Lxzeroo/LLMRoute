import pytest

from app.services.cache_validator import cache_validator


@pytest.mark.parametrize(
    "query,cached_query,expected",
    [
        (
            "Explain what Python is",
            "What is Python?",
            True
        ),
        (
            "Is Python not secure?",
            "Is Python secure?",
            False
        ),
        (
            "Calculate 20% of 500",
            "Calculate 10% of 500",
            False
        ),
        (
            "Explain Java 21",
            "Explain Java 17",
            False
        ),
        (
            "What is today's weather?",
            "What is today's weather?",
            False
        ),
        (
            "Implement binary search",
            "Explain binary search",
            False
        )
    ]
)
def test_cache_validation(query, cached_query, expected):

    valid, reason = cache_validator.validate(
        query, cached_query
    )

    assert valid == expected, reason
