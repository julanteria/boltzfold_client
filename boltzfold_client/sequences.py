"""Convenience helpers for working with FASTA files in client scripts."""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import TypeVar

_SeqTuple = tuple[str, str]
T = TypeVar("T")


def _normalize_sequence(text: str) -> str:
    cleaned = "".join(text.split()).upper()
    if not cleaned:
        raise ValueError("sequence is empty")
    return cleaned


def load_first_sequence(path: str | Path) -> str:
    """Return the first sequence stored in *path* (FASTA or plain text)."""
    p = Path(path).expanduser().resolve()
    lines = p.read_text().splitlines()
    seq: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if seq:
                break
            continue
        seq.append(line)
    if not seq:
        raise ValueError(f"{p} does not contain any sequence data")
    return _normalize_sequence("".join(seq))


def iter_fasta(path: str | Path) -> Iterator[_SeqTuple]:
    """Yield ``(name, sequence)`` pairs for every record in a FASTA file."""
    p = Path(path).expanduser().resolve()
    name: str | None = None
    seq: list[str] = []
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if name is not None:
                yield name, _normalize_sequence("".join(seq))
            name = line[1:].strip().split()[0]
            seq = []
        else:
            seq.append(line)
    if name is not None:
        yield name, _normalize_sequence("".join(seq))


def chunked(iterable: Iterable[T], size: int) -> Iterator[Sequence[T]]:
    """Yield fixed-size chunks from *iterable*."""
    if size < 1:
        raise ValueError("chunk size must be positive")
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, size))
        if not batch:
            return
        yield batch
