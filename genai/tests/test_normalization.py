"""Проверки доменной нормализации значений и цитат."""

import pytest

from app.modules.normalization import evidence_contains_value, normalize_evidence, normalize_value
from app.modules.registry import get_attribute


def test_normalizes_spaced_ocr_digits() -> None:
    attribute = get_attribute("DN")

    assert normalize_value("2 0 0", attribute) == "200"
    assert "200" in normalize_evidence("D N 2 0 0", attribute)
    assert evidence_contains_value("200", "D N 2 0 0", attribute)


def test_numeric_evidence_uses_complete_tokens() -> None:
    attribute = get_attribute("DN")

    assert normalize_evidence("DN 100 200", attribute) == "dn 100 200"
    assert evidence_contains_value("50", "DN 150", attribute) is False
    assert evidence_contains_value("100", "DN 100 200", attribute)


def test_normalizes_decimal_separator_and_trailing_zero() -> None:
    attribute = get_attribute("PN")

    assert normalize_value("4,0", attribute) == normalize_value("4.0", attribute) == "4"
    assert evidence_contains_value("4,0", "давление 4.0 МПа", attribute)
    assert evidence_contains_value("4", "давление 14.0 МПа", attribute) is False


@pytest.mark.parametrize("value", ["не число", "NaN", "1" * 17])
def test_rejects_invalid_numeric_values(value: str) -> None:
    assert normalize_value(value, get_attribute("PN")) is None


def test_normalizes_text_case_and_whitespace() -> None:
    attribute = get_attribute("MATERIAL")

    assert normalize_value("  Нержавеющая   СТАЛЬ ", attribute) == "нержавеющая сталь"
