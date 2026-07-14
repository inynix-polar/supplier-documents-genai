# Тестовое задание — Middle Gen-AI Engineer

Публичное решение задачи по извлечению атрибутов из технических документов поставщиков:
строгий structured output, few-shot prompting, post-LLM grounding и воспроизводимый
offline-eval baseline vs grounded.

Рабочее дерево намеренно содержит только выбранную задачу `genai/`. Остальные ролевые
заготовки из исходного архива удалены, чтобы ревьюеру не приходилось искать релевантный код;
исходный импорт сохранён в Git-истории.

## Куда смотреть

- [`genai/README.md`](genai/README.md) — условие, архитектура и команды запуска;
- [`genai/NOTES.md`](genai/NOTES.md) — решения, допущения, метрики и ограничения;
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — локальные проверки и Git/PR-процесс;
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — обязательный quality gate;
- [`genai/Dockerfile`](genai/Dockerfile) — изолированные test и eval runtime targets.

## Правила исходного задания

- **Формат:** vibe-coding; LLM-ассистент разрешён. Оцениваются декомпозиция, проверка
  результата модели и инженерные решения.
- **Тайм-бокс:** около 60 минут. Компромиссы и дальнейшие шаги фиксируются в `NOTES.md`.
- **Локальный запуск:** без внутренних репозиториев, секретов и тяжёлой инфраструктуры;
  LLM работает в режиме `LLM_FAKE=1`, eval использует синтетические данные.
- **Соглашения:** код и комментарии — на русском, термины и идентификаторы — на английском
  в `snake_case`, данные валидируются Pydantic, бизнес-правила вынесены в конфигурацию.
- **Git:** осмысленные Conventional Commits вместо одного гигантского коммита; изменения
  проходят через небольшие pull request.
- **`NOTES.md`:** обязательная часть решения с допущениями, компромиссами, дальнейшими
  шагами и фактическими командами проверки.

## Быстрый старт

```bash
uv sync --project genai --locked --all-groups
LLM_FAKE=1 uv run --directory genai --frozen python -m eval.run_eval --seed 42
```

Или через Docker:

```bash
docker build --file genai/Dockerfile --tag supplier-documents-genai:eval .
docker run --rm supplier-documents-genai:eval
```

Все обязательные критерии и закрытые бонусы перечислены в
[`genai/README.md`](genai/README.md); фактические результаты проверок — в
[`genai/NOTES.md`](genai/NOTES.md).
