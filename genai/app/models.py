"""Pydantic-контракты извлечения атрибутов."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

ConfidenceLevel = Literal["high", "medium", "low"]
RejectionReason = Literal[
    "invalid_model_response",
    "missing_source_quote",
    "source_quote_not_found",
    "value_not_supported_by_quote",
]


class LLMExtractionResponse(BaseModel):
    """Строгий внешний контракт ответа языковой модели."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    value: str | None
    unit: str | None
    confidence: ConfidenceLevel
    source_quote: str | None

    @field_validator("value", "unit", "source_quote")
    @classmethod
    def reject_blank_strings(cls, value: str | None) -> str | None:
        """Отличать отсутствие поля от опасной пустой строки."""
        if value is not None and not value.strip():
            raise ValueError("строковое поле не может быть пустым")
        return value

    @model_validator(mode="after")
    def validate_null_contract(self) -> Self:
        """Проверить согласованность результата «значение найдено/не найдено»."""
        if self.value is None:
            if self.unit is not None or self.source_quote is not None or self.confidence != "low":
                raise ValueError("для отсутствующего значения unit/source_quote должны быть null")
        elif self.source_quote is None:
            raise ValueError("найденное значение требует source_quote")
        return self


class ExtractedValue(BaseModel):
    """Итог извлечения после валидации и проверки источника."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str | None = None
    unit: str | None = None
    confidence: str | None = None
    source_quote: str | None = None
    rejected_reason: RejectionReason | None = None


class PromptExample(BaseModel):
    """Типизированный few-shot пример для системного промпта."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    attribute_code: str
    document: str
    response: LLMExtractionResponse
