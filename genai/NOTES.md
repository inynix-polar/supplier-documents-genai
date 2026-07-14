# NOTES

Заполни по ходу работы — это часть оценки.

## Что сделано
- Репозиторий инициализирован неизменённым scaffold-коммитом; работа ведётся в отдельной
  инфраструктурной ветке.
- Зависимости перенесены с `requirements.txt` на `uv`: добавлены `pyproject.toml`,
  `.python-version` и воспроизводимый `uv.lock`.
- Настроены Ruff, strict mypy с Pydantic-плагином, pytest/pytest-asyncio и branch coverage
  с минимальным порогом 80%.
- Добавлены локальные pre-commit/commit-msg/pre-push hooks и GitHub Actions для pull request
  и `main`.
- Добавлены 23 контрактных smoke-теста существующей заготовки; текущее покрытие — 98,8%.

## Решения и допущения
- `genai/` остаётся самостоятельным uv-проектом внутри исходной структуры архива, чтобы
  diff будущего pull request сохранял пути задания.
- Версия разработки — Python 3.12, минимально поддерживаемая — Python 3.11.
- `uv.lock` — единственный источник точных версий; параллельный `requirements.txt` удалён,
  чтобы зависимости не расходились.
- CI использует только `LLM_FAKE=1`, read-only `GITHUB_TOKEN`, ограничение времени и
  закреплённые SHA внешних actions.
- На инфраструктурном этапе исправлены только типы, форматирование, безопасный mutable
  default и загрузка eval-датасета относительно файла. Grounded-логика намеренно ещё не
  реализовывалась.

## Что не успел / сделал бы дальше
- Реализовать строгий structured output, few-shot prompt, retry и grounding-фильтр.
- Расширить eval-датасет и добавить детерминированное сравнение baseline vs grounded.
- После первой публикации настроить ruleset `main` с обязательным `CI / quality`.

## Как проверял
- `uv lock --check`.
- `uv run ruff check . ../scripts` и `uv run ruff format --check . ../scripts`.
- `uv run mypy` — strict-проверка без ошибок.
- `LLM_FAKE=1 uv run pytest` — 23 теста, 98,8% покрытия.
- `pre-commit run --all-files` и `pre-commit run --all-files --hook-stage pre-push`.
