"""Проверки внутри конвейера: ошибка вместо тихого «0 результатов».

Идея из SQLite (ALWAYS/NEVER, assert): в конце шага программа сама проверяет то,
что «не может не быть правдой». Здесь обычный raise, НЕ assert: `python -O`
выключает все assert, и проверка молча пропадёт.
"""
from __future__ import annotations

from collections.abc import Sized


class PipelineCheckError(RuntimeError):
    """Шаг конвейера получил невозможный результат."""


def ensure(condition: object, message: str) -> None:
    if not condition:
        raise PipelineCheckError(message)


def ensure_nonempty(items: Sized, step: str):
    """Пустой результат шага — ошибка, а не «ничего не нашлось»."""
    ensure(len(items) > 0, f"{step}: 0 результатов — шаг ничего не выдал")
    return items


def ensure_same_count(got: int, expected: int, what: str) -> None:
    """Сколько вошло, столько и вышло (файлов → матчей, строк → записей)."""
    ensure(got == expected, f"{what}: получено {got}, ожидалось {expected}")


def ensure_between(value: float, low: float, high: float, what: str) -> None:
    """Значение в разумных пределах (длительность матча, число игроков, %)."""
    ensure(low <= value <= high, f"{what} = {value}, вне [{low}, {high}]")
