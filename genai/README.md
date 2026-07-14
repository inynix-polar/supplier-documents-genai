# Тестовое задание — Middle Gen-AI Engineer

**Тайм-бокс:** ~60 минут · **Формат:** vibe-coding (LLM-ассистент разрешён)

> Самодостаточная заготовка: извлечение значений атрибутов из текста документов
> поставщика через LLM. `LLMClient` работает с `LLM_FAKE=1` без ключа и **намеренно
> иногда галлюцинирует** (возвращает значение, которого нет в тексте) — на этом
> проверяется твой грунтинг-фильтр.

## Контекст

Сейчас извлечение — «текст → JSON», JSON парсится best-effort
(`app/modules/extractor.py::extract_attribute_baseline`). Слабые места: модель может
выдумать значение, нет оценки уверенности, парсинг хрупкий.

## Задача

### 1. Надёжный извлекатель с грунтингом

Реализовать `extract_attribute_grounded` (`app/modules/extractor.py`, заглушка готова):
- few-shot промпт вынести в `app/prompts/extraction_prompts.py` (заготовка есть);
- строгий структурированный вывод: `value`, `unit`, `confidence` (high|medium|low),
  `source_quote` — дословная цитата из текста;
- **грунтинг-фильтр**: если `source_quote` не встречается в исходном тексте — извлечение
  отбраковывается (`value=None`, причина в `rejected_reason`). Это анти-галлюцинация;
- устойчивый парсинг JSON + осмысленный retry (клиент заворачивает ответ в ` ```json `).

> Клиент работает через OpenAI-совместимый chat-completions. Если используешь нативные
> structured outputs / tool-calling — оставь graceful fallback на JSON-парсинг.

### 2. Мини-эвал

`eval/dataset.jsonl` — 8 стартовых кейсов (есть OCR-шум, пропуск значения). Расширь
(противоречивые числа, ещё шум), в `eval/run_eval.py` сравни **baseline vs grounded**
по accuracy извлечения и **доле галлюцинаций**. Таблица + выводы.

`LLMClient` (`app/utils/llm_client.py`) с `LLM_FAKE=1` иногда возвращает значение без
цитаты в тексте — это и должен ловить грунтинг-фильтр.

## Запуск

```bash
uv sync --locked --all-groups
LLM_FAKE=1 uv run --frozen python -m eval.run_eval --seed 42
```

Eval использует одинаковый детерминированный fake-random поток для baseline и grounded на
каждом кейсе. Другой воспроизводимый сценарий можно получить через `--seed N`.

Проверки качества запускаются из директории `genai/`:

```bash
uv lock --check
uv run --frozen ruff check --config pyproject.toml . ../scripts
uv run --frozen ruff format --check --config pyproject.toml . ../scripts
uv run --frozen mypy
LLM_FAKE=1 uv run --frozen pytest
```

## Реализованное решение

Pipeline grounded extractor:

```text
registry/config → few-shot prompt → LLM → strict Pydantic parser → exact grounding → result
```

- документ сериализуется как недоверенное JSON-поле;
- direct и fenced JSON валидируются отдельной строгой моделью;
- schema error получает максимум одну contextual retry-попытку;
- ненулевое значение требует точную цитату и подтверждение значения внутри неё;
- baseline сохранён permissive для честного сравнения;
- 16-кейсовый eval считает метрики с явными знаменателями и печатает таблицы.

Результат при seed 42:

| Стратегия | Accuracy | Hallucinations / answered | Coverage |
|---|---:|---:|---:|
| baseline | 2/16 (12,5%) | 8/16 (50,0%) | 100,0% |
| grounded | 3/16 (18,8%) | 0/8 (0,0%) | 50,0% |

Grounding полностью убирает неподтверждённые ответы, но намеренно не скрывает остаточную
проблему: реальная цитата может содержать число, относящееся к другому атрибуту. Подробные
решения, знаменатели метрик и компромиссы описаны в [`NOTES.md`](NOTES.md).

## Критерии приёмки

- [x] Структурированный вывод (`value/unit/confidence/source_quote`), валидируется Pydantic.
- [x] Грунтинг-фильтр реально отсекает выдуманные значения.
- [x] Few-shot промпт вынесен в `app/prompts/`.
- [x] Устойчивый парсинг + осмысленный retry (не молчаливое проглатывание).
- [x] Эвал baseline vs grounded, метрика галлюцинаций, выводы.
- [x] Git-история с conventional commits + заполненный `NOTES.md`.

## Что оцениваем дополнительно (опиши в `NOTES.md`)

- Чем ещё борешься с галлюцинациями (температура, явный «не знаю»-выход).
- Стоимость/латентность: токены, можно ли батчить атрибуты в один вызов.
- Нативные structured outputs vs совместимость со старым endpoint.

## Бонусы (по желанию, плюс к оценке)

- **Базовый CI/CD** — GitHub Actions: линтер + `pytest` (с `LLM_FAKE=1`) на push/PR.
- **Docker** — `Dockerfile`, прогоняющий эвал/тесты в режиме `LLM_FAKE=1` без ключей.
- **Управление зависимостями** — `requirements.txt` оставлен как стартовая точка; плюсом
  будет перевод на **Poetry** (`pyproject.toml`).
- **Тесты** — на грунтинг-фильтр (отбраковка галлюцинации) и на устойчивость парсинга.
