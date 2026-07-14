# Разработка и pull request

## Требования

- Git;
- [uv](https://docs.astral.sh/uv/);
- доступ к Python 3.12 не обязателен: `uv` установит нужную версию автоматически.

## Первичная настройка

```bash
uv sync --project genai --locked --all-groups
uv run --project genai pre-commit install \
  --hook-type pre-commit \
  --hook-type commit-msg \
  --hook-type pre-push
```

`uv.lock` хранится в Git и вручную не редактируется. Зависимости добавляются командами
`uv add --project genai <package>` и `uv add --project genai --dev <package>`.

## Локальные проверки

Команды совпадают с GitHub Actions:

```bash
cd genai
uv lock --check
uv sync --locked --all-groups
uv run --frozen ruff check --config pyproject.toml . ../scripts
uv run --frozen ruff format --check --config pyproject.toml . ../scripts
uv run --frozen mypy
LLM_FAKE=1 uv run --frozen pytest
```

Все проверки сразу:

```bash
uv run --project genai pre-commit run --all-files
uv run --project genai pre-commit run --all-files --hook-stage pre-push
```

## Git-процесс

1. `main` остаётся стабильной и изменяется через pull request.
2. Для одного логического изменения создаётся отдельная ветка: `feat/...`, `fix/...`,
   `test/...`, `docs/...`, `chore/...`; ветки Codex имеют префикс `codex/`.
3. Коммиты следуют Conventional Commits, например
   `feat(extractor): добавить grounded-извлечение`.
4. Pull request сначала открывается как draft. Его заголовок также следует Conventional
   Commits и описывает итоговый эффект всего PR.
5. Перед переводом в ready должны проходить Ruff, mypy, pytest и проверка lock-файла.
6. Изменения бизнес-логики сопровождаются тестами и записью решений в `genai/NOTES.md`.

Для solo-репозитория достаточно нуля обязательных approvals, но обсуждения должны быть
разрешены, история — линейной, force-push и удаление `main` — запрещены. После первого
успешного CI check `CI / quality` следует сделать обязательным в ruleset ветки `main`.

## Соглашения проекта

- код и комментарии — на русском;
- термины и идентификаторы — на английском в `snake_case`;
- данные валидируются Pydantic;
- бизнес-правила не прячутся в случайных magic values;
- тесты и eval работают с `LLM_FAKE=1`, без секретов и внешней инфраструктуры.
