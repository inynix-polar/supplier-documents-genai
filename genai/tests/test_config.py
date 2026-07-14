"""Проверки конфигурации правил извлечения."""

import pytest
from pydantic import ValidationError

from app.config import DEFAULT_EXTRACTION_POLICY, ExtractionPolicy


def test_default_policy_limits_retry_count() -> None:
    assert DEFAULT_EXTRACTION_POLICY.max_attempts == 2
    assert DEFAULT_EXTRACTION_POLICY.require_exact_quote is True


def test_policy_rejects_invalid_attempt_count() -> None:
    with pytest.raises(ValidationError):
        ExtractionPolicy(max_attempts=0)


def test_policy_is_immutable() -> None:
    with pytest.raises(ValidationError, match="Instance is frozen"):
        DEFAULT_EXTRACTION_POLICY.max_attempts = 3  # type: ignore[misc]
