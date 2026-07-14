"""Контрактные тесты реестра атрибутов."""

import pytest

from app.modules.registry import AttributeDefinition, get_attribute
from app.prompts.extraction_prompts import EXTRACTION_SYSTEM, FEW_SHOT_EXAMPLES


def test_registry_exposes_attribute_metadata() -> None:
    attribute = get_attribute("DN")

    assert attribute.display_name == "Номинальный диаметр"
    assert attribute.unit == "мм"
    assert "Ду" in attribute.synonyms


def test_registry_raises_for_unknown_code() -> None:
    with pytest.raises(KeyError):
        get_attribute("UNKNOWN")


def test_synonyms_default_is_not_shared() -> None:
    first = AttributeDefinition(code="A", display_name="Первый")
    second = AttributeDefinition(code="B", display_name="Второй")

    first.synonyms.append("синоним")

    assert second.synonyms == []


def test_prompt_scaffold_exports_expected_contract() -> None:
    assert "source_quote" in EXTRACTION_SYSTEM
    assert FEW_SHOT_EXAMPLES == []
