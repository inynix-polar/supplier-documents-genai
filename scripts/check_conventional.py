"""Проверка заголовков коммитов и pull request по Conventional Commits."""

import argparse
import re
import subprocess
from pathlib import Path

TITLE_PATTERN = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"(\([a-z0-9][a-z0-9._/-]*\))?!?: [^\r\n]+$"
)
MAX_TITLE_LENGTH = 100


def is_conventional(title: str) -> bool:
    """Проверить формат и длину заголовка."""
    normalized = title.strip()
    return len(normalized) <= MAX_TITLE_LENGTH and TITLE_PATTERN.fullmatch(normalized) is not None


def read_commit_titles(commit_range: str) -> list[str]:
    """Получить первые строки сообщений коммитов из Git-диапазона."""
    result = subprocess.run(
        ["git", "log", "--format=%s", commit_range],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    """Разобрать источник проверяемых заголовков."""
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--message", help="Проверить переданную строку")
    source.add_argument("--file", type=Path, help="Прочитать сообщение коммита из файла")
    source.add_argument("--range", dest="commit_range", help="Проверить Git-диапазон")
    return parser.parse_args()


def main() -> int:
    """Вернуть ненулевой код, если хотя бы один заголовок некорректен."""
    args = parse_args()
    if args.message is not None:
        titles = [args.message]
    elif args.file is not None:
        titles = [args.file.read_text(encoding="utf-8").splitlines()[0]]
    else:
        titles = read_commit_titles(args.commit_range)

    invalid_titles = [title for title in titles if not is_conventional(title)]
    if not invalid_titles:
        return 0

    print("Некорректные заголовки Conventional Commits:")
    for title in invalid_titles:
        print(f"- {title}")
    print("Пример: feat(extractor): добавить grounded-извлечение")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
