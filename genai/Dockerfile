# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7

FROM ${PYTHON_IMAGE} AS uv-base

# Версия и multi-arch digest uv закреплены для воспроизводимой сборки.
COPY --from=ghcr.io/astral-sh/uv:0.11.28@sha256:0f36cb9361a3346885ca3677e3767016687b5a170c1a6b88465ec14aefec90aa /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Зависимости образуют отдельный кешируемый слой и проверяются по uv.lock.
COPY genai/pyproject.toml genai/uv.lock ./

FROM uv-base AS runtime-builder

ENV UV_NO_DEV=1

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

FROM uv-base AS test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --all-groups --no-install-project

COPY genai/app ./app
COPY genai/eval ./eval
COPY genai/tests ./tests
COPY scripts /scripts

ENV LLM_FAKE=1

CMD ["/app/.venv/bin/pytest"]

FROM ${PYTHON_IMAGE} AS runtime

LABEL org.opencontainers.image.source="https://github.com/inynix-polar/supplier-documents-genai" \
      org.opencontainers.image.title="supplier-documents-genai" \
      org.opencontainers.image.description="Offline-eval grounded extraction технических документов"

ENV HOME=/tmp \
    LLM_FAKE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=runtime-builder --chown=10001:10001 /app/.venv ./.venv
COPY --chown=10001:10001 genai/app ./app
COPY --chown=10001:10001 genai/eval ./eval

# Runtime не требует root и не содержит uv, тесты или исходный архив заданий.
USER 10001:10001

ENTRYPOINT ["python", "-m", "eval.run_eval"]
CMD ["--seed", "42"]
