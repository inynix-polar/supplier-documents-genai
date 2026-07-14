"""Pydantic-контракты извлечения атрибутов."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

ConfidenceLevel = Literal["high", "medium", "low"]


class LLMExtractionResponse(BaseModel):
    """Строгий внешний контракт ответа языковой модели."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    value: str | None
    unit: str | None
    confidence: ConfidenceLevel
    source_quote: str | None


class ExtractedValue(BaseModel):
    """Итог извлечения после валидации и проверки источника."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    value: str | None = None
    unit: str | None = None
    confidence: ConfidenceLevel | None = None
    source_quote: str | None = None
    rejected_reason: str | None = None


class PromptExample(BaseModel):
    """Типизированный few-shot пример для системного промпта."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    attribute_code: str
    document: str
    response: LLMExtractionResponse
