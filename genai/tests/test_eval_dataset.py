"""Проверки загрузки и валидации eval-датасета."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.extractor import ExtractedValue
from eval import run_eval
from eval.run_eval import EvalCase, load


def test_dataset_contains_valid_cases() -> None:
    cases = load()

    assert len(cases) == 8
    assert {case.attr for case in cases} == {"DN", "PN", "MATERIAL"}


def test_load_rejects_invalid_case(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text('{"text": "DN 100", "attr": "DN"}\n', encoding="utf-8")

    with pytest.raises(ValidationError):
        load(dataset_path)


@pytest.mark.asyncio
async def test_main_prints_baseline_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case = EvalCase(text="Задвижка DN 100.", attr="DN", expected="100")

    async def fake_extract(text: str, attr_code: str) -> ExtractedValue:
        assert text == case.text
        assert attr_code == case.attr
        return ExtractedValue(
            value="100",
            unit="мм",
            confidence="high",
            source_quote="DN 100",
        )

    monkeypatch.setattr(run_eval, "load", lambda: [case])
    monkeypatch.setattr(run_eval, "extract_attribute_baseline", fake_extract)

    await run_eval.main()

    assert "got=100" in capsys.readouterr().out
