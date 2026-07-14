"""Детерминированное сравнение baseline и grounded extraction."""

import argparse
import asyncio
import hashlib
import random
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import ExtractedValue
from app.modules.extractor import extract_attribute_baseline, extract_attribute_grounded
from app.modules.normalization import evidence_contains_value, normalize_value
from app.modules.registry import get_attribute
from app.utils.llm_client import CompletionClient, LLMClient
from eval.config import DEFAULT_EVAL_SETTINGS, EvalSettings

AttributeCode = Literal["DN", "PN", "MATERIAL"]
StrategyName = Literal["baseline", "grounded"]


class EvalCase(BaseModel):
    """Один валидируемый эталонный пример offline-eval."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: str = Field(min_length=1, pattern=r"^[a-z0-9_]+$")
    text: str = Field(min_length=1)
    attr: AttributeCode
    expected: str | None
    expected_unit: str | None
    tags: tuple[str, ...] = Field(min_length=1)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: tuple[str, ...]) -> tuple[str, ...]:
        """Не допускать пустые или повторяющиеся срезы датасета."""
        if any(not tag.strip() for tag in tags) or len(set(tags)) != len(tags):
            raise ValueError("tags должны быть непустыми и уникальными")
        return tags

    @model_validator(mode="after")
    def validate_expected_unit(self) -> Self:
        """Связать эталонную единицу с canonical unit из реестра."""
        canonical_unit = get_attribute(self.attr).unit
        if self.expected is None and self.expected_unit is not None:
            raise ValueError("отсутствующее значение не может иметь expected_unit")
        if self.expected is not None and self.expected_unit != canonical_unit:
            raise ValueError("expected_unit должна совпадать с canonical unit")
        return self


class EvalRow(BaseModel):
    """Парный результат двух стратегий на одном и том же кейсе."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    case: EvalCase
    baseline: ExtractedValue
    grounded: ExtractedValue
    baseline_calls: int = Field(ge=1)
    grounded_calls: int = Field(ge=1)


class EvalMetrics(BaseModel):
    """Счётчики и производные метрики одной стратегии."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    strategy: StrategyName
    total: int
    correct: int
    answered: int
    answered_correct: int
    grounding_violations: int
    negative_cases: int
    false_positives: int
    unit_cases: int
    unit_correct: int
    rejected: int
    total_calls: int

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> float:
        return numerator / denominator if denominator else 0.0

    @property
    def accuracy(self) -> float:
        return self._ratio(self.correct, self.total)

    @property
    def hallucination_rate(self) -> float:
        """Доля неподтверждённых ответов среди ненулевых ответов."""
        return self._ratio(self.grounding_violations, self.answered)

    @property
    def false_positive_rate(self) -> float:
        return self._ratio(self.false_positives, self.negative_cases)

    @property
    def unit_accuracy(self) -> float:
        return self._ratio(self.unit_correct, self.unit_cases)

    @property
    def coverage(self) -> float:
        return self._ratio(self.answered, self.total)

    @property
    def selective_accuracy(self) -> float:
        return self._ratio(self.answered_correct, self.answered)

    @property
    def rejection_rate(self) -> float:
        return self._ratio(self.rejected, self.total)

    @property
    def average_calls(self) -> float:
        return self._ratio(self.total_calls, self.total)


class CountingClient:
    """Посчитать вызовы, сохранив минимальный интерфейс LLM-клиента."""

    def __init__(self, delegate: CompletionClient) -> None:
        self.delegate = delegate
        self.call_count = 0

    async def complete(self, system: str, user: str) -> str:
        self.call_count += 1
        return await self.delegate.complete(system=system, user=user)


DATASET_PATH = Path(__file__).with_name("dataset.jsonl")


def load(path: Path = DATASET_PATH) -> list[EvalCase]:
    """Загрузить и строго провалидировать набор примеров."""
    return [
        EvalCase.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _case_seed(seed: int, case_id: str) -> int:
    """Получить стабильный seed, не зависящий от hash randomization Python."""
    digest = hashlib.sha256(f"{seed}:{case_id}".encode()).digest()
    return int.from_bytes(digest[:8], byteorder="big")


async def evaluate_case(case: EvalCase, settings: EvalSettings) -> EvalRow:
    """Выполнить честное парное сравнение на одинаковом fake-random потоке."""
    case_seed = _case_seed(settings.seed, case.id)
    baseline_client = CountingClient(
        LLMClient(
            rng=random.Random(case_seed),
            fake_delay_seconds=settings.fake_delay_seconds,
        )
    )
    grounded_client = CountingClient(
        LLMClient(
            rng=random.Random(case_seed),
            fake_delay_seconds=settings.fake_delay_seconds,
        )
    )

    baseline, grounded = await asyncio.gather(
        extract_attribute_baseline(case.text, case.attr, client=baseline_client),
        extract_attribute_grounded(case.text, case.attr, client=grounded_client),
    )
    return EvalRow(
        case=case,
        baseline=baseline,
        grounded=grounded,
        baseline_calls=baseline_client.call_count,
        grounded_calls=grounded_client.call_count,
    )


async def evaluate(
    cases: list[EvalCase],
    settings: EvalSettings = DEFAULT_EVAL_SETTINGS,
) -> list[EvalRow]:
    """Параллельно оценить кейсы с независимыми детерминированными клиентами."""
    return list(await asyncio.gather(*(evaluate_case(case, settings) for case in cases)))


def is_correct(case: EvalCase, result: ExtractedValue) -> bool:
    """Сравнить ожидаемое и извлечённое значение в доменной нормализации."""
    if case.expected is None or result.value is None:
        return case.expected is result.value
    attribute = get_attribute(case.attr)
    expected = normalize_value(case.expected, attribute)
    actual = normalize_value(result.value, attribute)
    return expected is not None and expected == actual


def has_grounding_violation(case: EvalCase, result: ExtractedValue) -> bool:
    """Определить принятый ответ без точного и содержательного evidence."""
    if result.value is None:
        return False
    source_quote = result.source_quote
    if not source_quote or source_quote not in case.text:
        return True
    return not evidence_contains_value(result.value, source_quote, get_attribute(case.attr))


def calculate_metrics(rows: list[EvalRow], strategy: StrategyName) -> EvalMetrics:
    """Посчитать метрики с явно заданными знаменателями."""
    results = [row.baseline if strategy == "baseline" else row.grounded for row in rows]
    calls = [row.baseline_calls if strategy == "baseline" else row.grounded_calls for row in rows]
    correct_flags = [
        is_correct(row.case, result) for row, result in zip(rows, results, strict=True)
    ]
    answered_flags = [result.value is not None for result in results]
    negative_flags = [row.case.expected is None for row in rows]
    unit_flags = [
        correct and result.value is not None and row.case.expected_unit is not None
        for row, result, correct in zip(rows, results, correct_flags, strict=True)
    ]

    return EvalMetrics(
        strategy=strategy,
        total=len(rows),
        correct=sum(correct_flags),
        answered=sum(answered_flags),
        answered_correct=sum(
            correct and answered
            for correct, answered in zip(correct_flags, answered_flags, strict=True)
        ),
        grounding_violations=sum(
            has_grounding_violation(row.case, result)
            for row, result in zip(rows, results, strict=True)
        ),
        negative_cases=sum(negative_flags),
        false_positives=sum(
            negative and answered
            for negative, answered in zip(negative_flags, answered_flags, strict=True)
        ),
        unit_cases=sum(unit_flags),
        unit_correct=sum(
            unit_expected
            and result.unit is not None
            and result.unit.strip().casefold() == row.case.expected_unit.strip().casefold()
            for row, result, unit_expected in zip(rows, results, unit_flags, strict=True)
            if row.case.expected_unit is not None
        ),
        rejected=sum(result.rejected_reason is not None for result in results),
        total_calls=sum(calls),
    )


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _value(value: str | None) -> str:
    return value if value is not None else "∅"


def render_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    """Сформировать компактную Markdown-таблицу без внешней зависимости."""
    escaped_rows = [tuple(cell.replace("|", r"\|") for cell in row) for row in rows]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in escaped_rows))
        for index in range(len(headers))
    ]

    def render_row(row: tuple[str, ...]) -> str:
        cells = (cell.ljust(widths[index]) for index, cell in enumerate(row))
        return f"| {' | '.join(cells)} |"

    separator = tuple("-" * width for width in widths)
    return "\n".join(
        (render_row(headers), render_row(separator), *(render_row(row) for row in escaped_rows))
    )


def render_report(rows: list[EvalRow], seed: int) -> str:
    """Собрать таблицы и выводы для воспроизводимого CLI-отчёта."""
    baseline = calculate_metrics(rows, "baseline")
    grounded = calculate_metrics(rows, "grounded")
    case_rows: list[tuple[str, ...]] = [
        (
            row.case.id,
            _value(row.case.expected),
            _value(row.baseline.value),
            _value(row.grounded.value),
            "да" if has_grounding_violation(row.case, row.baseline) else "нет",
            row.grounded.rejected_reason or "—",
        )
        for row in rows
    ]
    summary_rows: list[tuple[str, ...]] = [
        (
            metrics.strategy,
            f"{metrics.correct}/{metrics.total} ({_percent(metrics.accuracy)})",
            (
                f"{metrics.grounding_violations}/{metrics.answered} "
                f"({_percent(metrics.hallucination_rate)})"
            ),
            f"{metrics.false_positives}/{metrics.negative_cases}",
            f"{metrics.unit_correct}/{metrics.unit_cases} ({_percent(metrics.unit_accuracy)})",
            f"{metrics.answered}/{metrics.total} ({_percent(metrics.coverage)})",
            _percent(metrics.selective_accuracy),
            f"{metrics.rejected}/{metrics.total} ({_percent(metrics.rejection_rate)})",
            f"{metrics.average_calls:.2f}",
        )
        for metrics in (baseline, grounded)
    ]
    accuracy_delta = (grounded.accuracy - baseline.accuracy) * 100
    hallucination_delta = (grounded.hallucination_rate - baseline.hallucination_rate) * 100
    conclusions = [
        (
            "grounded не принял ни одной неподтверждённой цитаты"
            if grounded.grounding_violations == 0
            else "grounded всё ещё принимает неподтверждённые ответы"
        ),
        f"изменение accuracy: {accuracy_delta:+.1f} п.п.",
        f"изменение hallucination rate: {hallucination_delta:+.1f} п.п.",
        (
            "наличие evidence не гарантирует семантически верный выбор числа; "
            "это видно отдельно по accuracy"
        ),
    ]

    return "\n\n".join(
        (
            f"Seed: {seed}; кейсов: {len(rows)}",
            render_table(
                ("case", "expected", "baseline", "grounded", "B violation", "G rejection"),
                case_rows,
            ),
            render_table(
                (
                    "strategy",
                    "accuracy",
                    "hallucinations/answered",
                    "false positives",
                    "unit acc on correct",
                    "coverage",
                    "selective acc",
                    "rejections",
                    "avg calls",
                ),
                summary_rows,
            ),
            "Выводы:\n" + "\n".join(f"- {conclusion}" for conclusion in conclusions),
        )
    )


async def main(settings: EvalSettings = DEFAULT_EVAL_SETTINGS) -> None:
    """Запустить eval и напечатать воспроизводимый отчёт."""
    rows = await evaluate(load(), settings)
    print(render_report(rows, settings.seed))


def parse_args() -> argparse.Namespace:
    """Разобрать CLI-параметры eval."""
    parser = argparse.ArgumentParser(description="Сравнение baseline и grounded extraction")
    parser.add_argument("--seed", type=int, default=DEFAULT_EVAL_SETTINGS.seed)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(DEFAULT_EVAL_SETTINGS.model_copy(update={"seed": args.seed})))
