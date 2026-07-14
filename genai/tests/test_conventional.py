"""Тесты правил именования коммитов и pull request."""

import pytest

from scripts.check_conventional import is_conventional


@pytest.mark.parametrize(
    "title",
    [
        "feat: добавить извлечение",
        "fix(parser): обработать fenced JSON",
        "refactor(extractor)!: изменить контракт",
    ],
)
def test_accepts_conventional_title(title: str) -> None:
    assert is_conventional(title)


@pytest.mark.parametrize(
    "title",
    [
        "добавить извлечение",
        "Feat: неверный регистр",
        "feat(НЕВЕРНО): кириллица в scope",
        "feat: " + "x" * 101,
    ],
)
def test_rejects_non_conventional_title(title: str) -> None:
    assert not is_conventional(title)
