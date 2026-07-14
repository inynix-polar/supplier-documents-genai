"""Нормализация значений для сравнения без изменения исходной цитаты."""

import re
import unicodedata
from decimal import Decimal, InvalidOperation

from app.modules.registry import AttributeDefinition

_WHITESPACE_RE = re.compile(r"\s+")
_SPACED_DIGITS_RE = re.compile(r"(?<=\d)\s+(?=\d)")
_DECIMAL_COMMA_RE = re.compile(r"(?<=\d),(?=\d)")


def _normalize_unicode(value: str) -> str:
    """Привести Unicode и пробелы к устойчивому виду."""
    normalized = unicodedata.normalize("NFKC", value).strip()
    return _WHITESPACE_RE.sub(" ", normalized)


def normalize_value(value: str, attribute: AttributeDefinition) -> str:
    """Нормализовать значение согласно типу атрибута из реестра."""
    normalized = _normalize_unicode(value)

    if attribute.value_kind == "integer":
        return _SPACED_DIGITS_RE.sub("", normalized)

    if attribute.value_kind == "decimal":
        decimal_text = _DECIMAL_COMMA_RE.sub(".", normalized)
        try:
            number = Decimal(decimal_text)
        except InvalidOperation:
            return decimal_text.casefold()
        return format(number.normalize(), "f")

    return normalized.casefold()


def normalize_evidence(text: str, attribute: AttributeDefinition) -> str:
    """Нормализовать цитату только для семантической проверки значения."""
    normalized = _normalize_unicode(text).casefold()
    if attribute.value_kind == "integer":
        return _SPACED_DIGITS_RE.sub("", normalized)
    if attribute.value_kind == "decimal":
        return _DECIMAL_COMMA_RE.sub(".", normalized)
    return normalized
