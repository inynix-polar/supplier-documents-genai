"""
Скелет мини-эвала.

Задача: расширить датасет (OCR-шум, противоречивые числа, отсутствие значения),
сравнить baseline vs grounded по accuracy извлечения и доле ГАЛЛЮЦИНАЦИЙ
(value, которого нет в тексте).

Запуск:  python -m eval.run_eval
"""

import asyncio
from pathlib import Path

from pydantic import BaseModel

from app.modules.extractor import extract_attribute_baseline


class EvalCase(BaseModel):
    """Один эталонный пример для offline-оценки."""

    text: str
    attr: str
    expected: str | None


DATASET_PATH = Path(__file__).with_name("dataset.jsonl")


def load(path: Path = DATASET_PATH) -> list[EvalCase]:
    """Загрузить и провалидировать набор примеров."""
    return [
        EvalCase.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


async def main() -> None:
    rows = load()
    for row in rows:
        res = await extract_attribute_baseline(row.text, row.attr)
        hallucinated = bool(res.value) and (res.source_quote or "") not in row.text
        print(
            f"exp={str(row.expected):28} got={str(res.value):8} "
            f"hallucinated={hallucinated}  quote={res.source_quote!r}"
        )

    # TODO(кандидат): accuracy + доля галлюцинаций для baseline vs grounded; таблица + вывод.


if __name__ == "__main__":
    asyncio.run(main())
