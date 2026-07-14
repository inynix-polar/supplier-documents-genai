"""Проверки метрик и табличного отчёта baseline vs grounded."""

from app.models import ExtractedValue
from eval.run_eval import (
    EvalCase,
    EvalRow,
    calculate_metrics,
    has_grounding_violation,
    render_report,
)


def rows() -> list[EvalRow]:
    """Собрать пару кейсов с известными счётчиками."""
    positive = EvalCase(
        id="dn_positive",
        text="Задвижка DN 100.",
        attr="DN",
        expected="100",
        expected_unit="мм",
        tags=("positive",),
    )
    negative = EvalCase(
        id="pn_negative",
        text="Давление не указано.",
        attr="PN",
        expected=None,
        expected_unit=None,
        tags=("negative",),
    )
    hallucination = ExtractedValue(
        value="999",
        unit="мм",
        confidence="high",
        source_quote="значение из справочника",
    )
    rejection = ExtractedValue(
        value=None,
        unit=None,
        confidence="high",
        source_quote="значение из справочника",
        rejected_reason="source_quote_not_found",
    )
    return [
        EvalRow(
            case=positive,
            baseline=hallucination,
            grounded=ExtractedValue(
                value="100",
                unit="мм",
                confidence="high",
                source_quote="DN 100",
            ),
            baseline_calls=1,
            grounded_calls=1,
        ),
        EvalRow(
            case=negative,
            baseline=hallucination,
            grounded=rejection,
            baseline_calls=1,
            grounded_calls=1,
        ),
    ]


def test_calculates_metrics_with_explicit_denominators() -> None:
    eval_rows = rows()

    baseline = calculate_metrics(eval_rows, "baseline")
    grounded = calculate_metrics(eval_rows, "grounded")

    assert baseline.accuracy == 0
    assert baseline.hallucination_rate == 1
    assert baseline.false_positive_rate == 1
    assert grounded.accuracy == 1
    assert grounded.hallucination_rate == 0
    assert grounded.coverage == 0.5
    assert grounded.selective_accuracy == 1
    assert grounded.unit_accuracy == 1
    assert grounded.rejection_rate == 0.5
    assert grounded.average_calls == 1


def test_missing_quote_is_grounding_violation() -> None:
    case = rows()[0].case
    result = ExtractedValue(value="100", unit="мм", confidence="high", source_quote=None)

    assert has_grounding_violation(case, result)


def test_report_contains_tables_metrics_and_conclusions() -> None:
    report = render_report(rows(), seed=42)

    assert "Seed: 42; кейсов: 2" in report
    assert "hallucinations/answered" in report
    assert "baseline" in report
    assert "grounded" in report
    assert "изменение accuracy: +100.0 п.п." in report
    assert "изменение hallucination rate: -100.0 п.п." in report
    assert "grounded не принял ни одной неподтверждённой цитаты" in report
