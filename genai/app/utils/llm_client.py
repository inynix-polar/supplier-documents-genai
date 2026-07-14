"""
LLM-клиент поверх OpenAI-совместимого chat-completions.

С LLM_FAKE=1 (по умолчанию) возвращает правдоподобные ответы — иногда с
галлюцинацией (значение, которого нет в тексте), чтобы грунтинг-фильтр было на чём
проверить, и можно было работать без живого ключа.
"""

import asyncio
import json
import os
import random
import re
from typing import Protocol, cast


class CompletionClient(Protocol):
    """Минимальный интерфейс клиента для dependency injection и тестов."""

    async def complete(self, system: str, user: str) -> str:
        """Вернуть текстовый ответ модели."""
        ...


def _extract_document(user: str) -> str:
    """Получить document из JSON-запроса или сохранить legacy-текст baseline."""
    try:
        payload: object = json.loads(user)
    except json.JSONDecodeError:
        return user
    if isinstance(payload, dict):
        document = cast(dict[object, object], payload).get("document")
        if isinstance(document, str):
            return document
    return user


class LLMClient:
    def __init__(self) -> None:
        self.fake = os.getenv("LLM_FAKE", "1") == "1"

    async def complete(self, system: str, user: str) -> str:
        if self.fake:
            await asyncio.sleep(0.05)
            # Пытаемся «извлечь» число из документа; в 25% случаев галлюцинируем.
            document = _extract_document(user)
            m = re.search(r"(\d+(?:[.,]\d+)?)", document)
            if m and random.random() > 0.25:
                value = m.group(1)
                quote = document[max(0, m.start() - 10) : m.end() + 10].strip()
            else:
                value = "999"  # значения нет в тексте (галлюцинация)
                quote = "значение из справочника"  # цитаты в тексте нет
            return (
                "```json\n"
                + json.dumps(
                    {"value": value, "unit": "мм", "confidence": "high", "source_quote": quote},
                    ensure_ascii=False,
                )
                + "\n```"
            )
        raise NotImplementedError("Подключи endpoint или используй LLM_FAKE=1")
