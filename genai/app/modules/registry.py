"""Мини-реестр атрибутов и правил нормализации."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

ValueKind = Literal["integer", "decimal", "text"]


class AttributeDefinition(BaseModel):
    """Неизменяемая конфигурация одного извлекаемого атрибута."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    code: str
    display_name: str
    value_kind: ValueKind
    unit: str | None = None
    synonyms: tuple[str, ...] = ()


_ATTRS = {
    "DN": AttributeDefinition(
        code="DN",
        display_name="Номинальный диаметр",
        value_kind="integer",
        unit="мм",
        synonyms=("условный проход", "Ду", "DN", "DY"),
    ),
    "PN": AttributeDefinition(
        code="PN",
        display_name="Условное давление",
        value_kind="decimal",
        unit="МПа",
        synonyms=("рабочее давление", "Ру", "PN"),
    ),
    "MATERIAL": AttributeDefinition(
        code="MATERIAL",
        display_name="Материал корпуса",
        value_kind="text",
        synonyms=("материал", "исполнение", "сталь"),
    ),
}


def get_attribute(code: str) -> AttributeDefinition:
    return _ATTRS[code]
