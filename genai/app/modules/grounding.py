"""Проверка того, что извлечённое значение подтверждено исходным документом."""

from app.config import DEFAULT_EXTRACTION_POLICY, ExtractionPolicy
from app.models import ExtractedValue, LLMExtractionResponse, RejectionReason
from app.modules.normalization import evidence_contains_value
from app.modules.registry import AttributeDefinition


def _reject(
    response: LLMExtractionResponse,
    reason: RejectionReason,
) -> ExtractedValue:
    """Сформировать аудируемый отказ без принятого значения."""
    return ExtractedValue(
        value=None,
        unit=None,
        confidence=response.confidence,
        source_quote=response.source_quote,
        rejected_reason=reason,
    )


def ground_response(
    response: LLMExtractionResponse,
    text: str,
    attribute: AttributeDefinition,
    policy: ExtractionPolicy = DEFAULT_EXTRACTION_POLICY,
) -> ExtractedValue:
    """Применить обязательную exact-quote и дополнительную semantic-проверку."""
    if response.value is None:
        return ExtractedValue(confidence=response.confidence)

    source_quote = response.source_quote
    if source_quote is None:
        return _reject(response, "missing_source_quote")
    if source_quote not in text:
        return _reject(response, "source_quote_not_found")
    if policy.verify_value_in_quote and not evidence_contains_value(
        response.value,
        source_quote,
        attribute,
    ):
        return _reject(response, "value_not_supported_by_quote")

    return ExtractedValue(
        value=response.value,
        unit=response.unit,
        confidence=response.confidence,
        source_quote=source_quote,
    )
