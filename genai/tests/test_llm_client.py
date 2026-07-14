"""Проверки локального fake-режима LLM-клиента."""

import json
import random

import pytest

from app.modules.extractor import _loose_json
from app.utils.llm_client import LLMClient


@pytest.mark.asyncio
async def test_fake_client_extracts_first_number(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")
    monkeypatch.setattr(random, "random", lambda: 0.5)

    raw = await LLMClient().complete(system="", user="Текст: DN 100")

    assert _loose_json(raw) == {
        "value": "100",
        "unit": "мм",
        "confidence": "high",
        "source_quote": "Текст: DN 100",
    }


@pytest.mark.asyncio
async def test_fake_client_can_hallucinate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")
    monkeypatch.setattr(random, "random", lambda: 0.0)

    raw = await LLMClient().complete(system="", user="Текст: DN 100")

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
    monkeypatch.setattr(random, "random", lambda: 0.5)
    user = json.dumps({"attribute": {"code": "DN"}, "document": "Задвижка DN 100."})

    raw = await LLMClient().complete(system="", user=user)

    assert _loose_json(raw) == {
        "value": "100",
        "unit": "мм",
        "confidence": "high",
        "source_quote": "движка DN 100.",
    }


@pytest.mark.asyncio
async def test_live_client_is_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "0")

    with pytest.raises(NotImplementedError, match="LLM_FAKE=1"):
        await LLMClient().complete(system="", user="")
