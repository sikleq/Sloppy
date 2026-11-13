"""Запись «всё или ничего»: файл либо старый целиком, либо новый целиком.

Идея из SQLite (atomic commit): пишем во временный файл рядом, сбрасываем на
диск, затем одной операцией подменяем. Обрыв процесса посреди записи оставляет
старый файл нетронутым (и, возможно, лишний *.tmp — его можно удалить).
"""
from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

_REPLACE_RETRIES = 5        # Windows: антивирус/читатель держит файл
_REPLACE_PAUSE_S = 0.05


def atomic_write_bytes(path: str | os.PathLike, data: bytes) -> None:
    target = Path(path)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        _replace_with_retry(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def atomic_write_text(path: str | os.PathLike, text: str, encoding: str = "utf-8") -> None:
    atomic_write_bytes(path, text.encode(encoding))


def _replace_with_retry(src: str, dst: Path) -> None:
    for attempt in range(_REPLACE_RETRIES):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == _REPLACE_RETRIES - 1:
                raise
            time.sleep(_REPLACE_PAUSE_S)
