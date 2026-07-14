"""Конфигурация бизнес-правил извлечения."""

from pydantic import BaseModel, ConfigDict, Field


class ExtractionPolicy(BaseModel):
    """Ограничения повторных попыток и проверки подтверждающей цитаты."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    max_attempts: int = Field(default=2, ge=1, le=3)
    require_exact_quote: bool = True
    verify_value_in_quote: bool = True


DEFAULT_EXTRACTION_POLICY = ExtractionPolicy()
