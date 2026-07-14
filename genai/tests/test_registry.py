"""Контрактные тесты реестра атрибутов."""

import pytest
from pydantic import ValidationError

from app.modules.registry import get_attribute


def test_registry_exposes_attribute_metadata() -> None:
    attribute = get_attribute("DN")

    assert attribute.display_name == "Номинальный диаметр"
    assert attribute.unit == "мм"
    assert "Ду" in attribute.synonyms


def test_registry_raises_for_unknown_code() -> None:
    with pytest.raises(KeyError):
        get_attribute("UNKNOWN")


def test_registry_configuration_is_immutable() -> None:
    attribute = get_attribute("DN")

    with pytest.raises(ValidationError, match="Instance is frozen"):
        attribute.unit = "см"  # type: ignore[misc]
