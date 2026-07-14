"""Проверки загрузки и воспроизводимого запуска eval-датасета."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from eval import run_eval
from eval.config import EvalSettings
from eval.run_eval import EvalCase, calculate_metrics, evaluate, load


def test_dataset_contains_expanded_unique_cases() -> None:
    cases = load()

    assert len(cases) == 16
    assert len({case.id for case in cases}) == len(cases)
    assert {case.attr for case in cases} == {"DN", "PN", "MATERIAL"}
    assert sum("negative" in case.tags for case in cases) >= 3
    assert sum("ocr" in case.tags for case in cases) >= 3
    assert any("conflict" in case.tags for case in cases)


def test_load_rejects_invalid_case(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text('{"text": "DN 100", "attr": "DN"}\n', encoding="utf-8")

    with pytest.raises(ValidationError):
        load(dataset_path)


@pytest.mark.asyncio
async def test_evaluate_is_reproducible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")
    cases = [load()[0], load()[4]]
    settings = EvalSettings(seed=17, fake_delay_seconds=0)

    first = await evaluate(cases, settings)
    second = await evaluate(cases, settings)

    assert first == second
    assert all(row.baseline_calls == row.grounded_calls == 1 for row in first)


@pytest.mark.asyncio
async def test_grounded_eval_meets_relative_acceptance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")
    eval_rows = await evaluate(load(), EvalSettings(seed=42, fake_delay_seconds=0))

    baseline = calculate_metrics(eval_rows, "baseline")
    grounded = calculate_metrics(eval_rows, "grounded")

    assert baseline.grounding_violations > 0
    assert grounded.grounding_violations == 0
    assert grounded.accuracy >= baseline.accuracy
    assert grounded.selective_accuracy >= baseline.selective_accuracy


@pytest.mark.asyncio
async def test_main_prints_rendered_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case = EvalCase(
        id="dn_test",
        text="Задвижка DN 100.",
        attr="DN",
        expected="100",
        expected_unit="мм",
        tags=("positive",),
    )

    async def fake_evaluate(
        cases: list[EvalCase], settings: EvalSettings
    ) -> list[run_eval.EvalRow]:
        assert cases == [case]
        assert settings.seed == 7
        return []

    monkeypatch.setattr(run_eval, "load", lambda: [case])
    monkeypatch.setattr(run_eval, "evaluate", fake_evaluate)
    monkeypatch.setattr(run_eval, "render_report", lambda rows, seed: f"отчёт seed={seed}")

    await run_eval.main(EvalSettings(seed=7))

    assert capsys.readouterr().out == "отчёт seed=7\n"
