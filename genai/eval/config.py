"""Воспроизводимая конфигурация offline-eval."""

from pydantic import BaseModel, ConfigDict, Field


class EvalSettings(BaseModel):
    """Параметры парного запуска baseline и grounded."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    seed: int = 42
    fake_delay_seconds: float = Field(default=0.0, ge=0)


DEFAULT_EVAL_SETTINGS = EvalSettings()
