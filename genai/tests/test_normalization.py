"""Проверки доменной нормализации значений и цитат."""

from app.modules.normalization import normalize_evidence, normalize_value
from app.modules.registry import get_attribute


def test_normalizes_spaced_ocr_digits() -> None:
    attribute = get_attribute("DN")

    assert normalize_value("2 0 0", attribute) == "200"
    assert "200" in normalize_evidence("D N 2 0 0", attribute)


def test_normalizes_decimal_separator_and_trailing_zero() -> None:
    attribute = get_attribute("PN")

    assert normalize_value("4,0", attribute) == normalize_value("4.0", attribute) == "4"


def test_normalizes_text_case_and_whitespace() -> None:
    attribute = get_attribute("MATERIAL")

    assert normalize_value("  Нержавеющая   СТАЛЬ ", attribute) == "нержавеющая сталь"
