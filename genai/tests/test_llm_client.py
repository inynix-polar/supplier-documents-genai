"""Проверки локального fake-режима LLM-клиента."""

import json
import random

import pytest

from app.modules.extractor import _loose_json
from app.utils.llm_client import LLMClient


@pytest.mark.asyncio
async def test_fake_client_extracts_first_number(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")

    raw = await LLMClient(
        rng=random.Random(0),
        fake_delay_seconds=0,
    ).complete(system="", user="Текст: DN 100")

    assert _loose_json(raw) == {
        "value": "100",
        "unit": "мм",
        "confidence": "high",
        "source_quote": "DN 100",
    }


@pytest.mark.asyncio
async def test_fake_client_can_hallucinate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")

    raw = await LLMClient(
        rng=random.Random(1),
        fake_delay_seconds=0,
    ).complete(system="", user="Текст: DN 100")

    assert _loose_json(raw) == {
        "value": "999",
        "unit": "мм",
        "confidence": "high",
        "source_quote": "значение из справочника",
    }


@pytest.mark.asyncio
async def test_fake_client_reads_document_from_json_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")
    user = json.dumps({"attribute": {"code": "DN"}, "document": "Задвижка DN 100."})

    raw = await LLMClient(
        rng=random.Random(0),
        fake_delay_seconds=0,
    ).complete(system="", user=user)

    assert _loose_json(raw) == {
        "value": "100",
        "unit": "мм",
        "confidence": "high",
        "source_quote": "движка DN 100.",
    }


@pytest.mark.asyncio
async def test_fake_client_uses_canonical_unit_from_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")
    user = json.dumps(
        {
            "attribute": {"code": "PN", "canonical_unit": "МПа"},
            "document": "Рабочее давление PN 16 МПа.",
        },
        ensure_ascii=False,
    )

    raw = await LLMClient(
        rng=random.Random(0),
        fake_delay_seconds=0,
    ).complete(system="", user=user)
    payload = _loose_json(raw)

    assert payload is not None
    assert payload["unit"] == "МПа"


@pytest.mark.asyncio
async def test_fake_client_is_reproducible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")
    clients = [
        LLMClient(rng=random.Random(42), fake_delay_seconds=0),
        LLMClient(rng=random.Random(42), fake_delay_seconds=0),
    ]

    responses = [await client.complete(system="", user="Текст: DN 100") for client in clients]

    assert responses[0] == responses[1]


def test_fake_client_rejects_negative_delay() -> None:
    with pytest.raises(ValueError, match="отрицательной"):
        LLMClient(fake_delay_seconds=-0.1)


@pytest.mark.asyncio
async def test_live_client_is_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "0")

    with pytest.raises(NotImplementedError, match="LLM_FAKE=1"):
        await LLMClient().complete(system="", user="")
