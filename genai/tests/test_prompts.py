"""Проверки системного и пользовательского промптов извлечения."""

from app.modules.registry import get_attribute
from app.prompts.extraction_prompts import (
    EXTRACTION_SYSTEM,
    FEW_SHOT_EXAMPLES,
    build_system_prompt,
    build_user_prompt,
)


def test_prompt_contains_contract_and_few_shot_examples() -> None:
    assert "source_quote" in EXTRACTION_SYSTEM
    assert len(FEW_SHOT_EXAMPLES) == 2
    assert "DN 100" in build_system_prompt()
    assert '"value":null' in build_system_prompt()


def test_user_prompt_contains_attribute_configuration_and_document() -> None:
    prompt = build_user_prompt("Задвижка DN 100.", get_attribute("DN"))

    assert "Номинальный диаметр" in prompt
    assert "условный проход" in prompt
    assert "<document>\nЗадвижка DN 100.\n</document>" in prompt
