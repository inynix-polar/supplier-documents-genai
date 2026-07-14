"""Нормализация значений для сравнения без изменения исходной цитаты."""

import re
import unicodedata
from decimal import Decimal, InvalidOperation

from app.modules.registry import AttributeDefinition

_WHITESPACE_RE = re.compile(r"\s+")
_SPACED_SINGLE_DIGITS_RE = re.compile(r"(?<!\d)(?:\d\s+)+\d(?!\d)")
_DECIMAL_COMMA_RE = re.compile(r"(?<=\d),(?=\d)")
_INTEGER_RE = re.compile(r"\d+")
_DECIMAL_RE = re.compile(r"\d+(?:[.,]\d+)?")


def _normalize_unicode(value: str) -> str:
    """Привести Unicode и пробелы к устойчивому виду."""
    normalized = unicodedata.normalize("NFKC", value).strip()
    return _WHITESPACE_RE.sub(" ", normalized)


def _collapse_spaced_digits(value: str) -> str:
    """Схлопнуть только OCR-последовательности из одиночных цифр."""
    return _SPACED_SINGLE_DIGITS_RE.sub(
        lambda match: re.sub(r"\s+", "", match.group()),
        value,
    )


def normalize_value(value: str, attribute: AttributeDefinition) -> str | None:
    """Нормализовать значение согласно типу атрибута из реестра."""
    normalized = _normalize_unicode(value)
    if len(normalized) > attribute.max_value_length:
        return None

    if attribute.value_kind == "integer":
        integer_text = _collapse_spaced_digits(normalized)
        if _INTEGER_RE.fullmatch(integer_text) is None:
            return None
        return str(int(integer_text))

    if attribute.value_kind == "decimal":
        decimal_text = _DECIMAL_COMMA_RE.sub(".", normalized)
        if _DECIMAL_RE.fullmatch(decimal_text) is None:
            return None
        try:
            number = Decimal(decimal_text)
        except InvalidOperation:
            return None
        if not number.is_finite():
            return None
        return format(number.normalize(), "f")

    return normalized.casefold()


def normalize_evidence(text: str, attribute: AttributeDefinition) -> str:
    """Нормализовать цитату только для семантической проверки значения."""
    normalized = _normalize_unicode(text).casefold()
    if attribute.value_kind == "integer":
        return _collapse_spaced_digits(normalized)
    if attribute.value_kind == "decimal":
        return _DECIMAL_COMMA_RE.sub(".", normalized)
    return normalized


def evidence_contains_value(
    value: str,
    source_quote: str,
    attribute: AttributeDefinition,
) -> bool:
    """Проверить значение по целым числовым токенам или нормализованному тексту."""
    normalized_value = normalize_value(value, attribute)
    if normalized_value is None:
        return False

    evidence = normalize_evidence(source_quote, attribute)
    if attribute.value_kind == "integer":
        return any(str(int(token)) == normalized_value for token in _INTEGER_RE.findall(evidence))
    if attribute.value_kind == "decimal":
        return any(
            normalize_value(token, attribute) == normalized_value
            for token in _DECIMAL_RE.findall(evidence)
        )
    return normalized_value in evidence
