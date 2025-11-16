"""Utilities for printing live job status in notebooks or terminals."""

from __future__ import annotations

import itertools
import shutil
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .client import BoltzFoldClient
from .models import JobStatus, JobSummary

try:  # pragma: no cover - optional
    from IPython.display import clear_output as _ipython_clear
except ImportError:  # pragma: no cover - optional
    _ipython_clear = None  # type: ignore[assignment]


SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


def _terminal_width(default: int = 40) -> int:
    try:
        return shutil.get_terminal_size().columns
    except OSError:  # pragma: no cover - defensive
        return default


@dataclass
class LiveJobPrinter:
    """Minimalist status renderer that works in both notebooks and plain terminals."""

    title: str = "BoltzFold Job Monitor"
    spinner_frames: Iterable[str] = SPINNER_FRAMES
    show_message: bool = True
    auto_clear: bool = True

    def __post_init__(self) -> None:
        self._spinner = itertools.cycle(self.spinner_frames)

    def render(self, status: JobStatus, elapsed_seconds: float, extra: str | None = None) -> None:
        frame = next(self._spinner)
        width = max(52, min(96, _terminal_width()))
        inner = width - 2
        content = inner - 2
        bar = "═" * inner
        if self.auto_clear:
            self._clear()

        def line(text: str = "") -> None:
            print(f"║ {text:<{content}} ║")

        title = f"✶ {self.title} ✶"
        print(f"╔{bar}╗")
        line(title.center(content))
        print(f"╠{bar}╣")
        line(f"Job ID     : {status.job_id}")
        line(f"Status     : {frame} {status.status.upper()}")
        line(f"Elapsed    : {elapsed_seconds:6.1f} s")
        if self.show_message and status.message:
            line(self._format_message(status.message, content))
        if status.status == "succeeded":
            line("🚀  Docking complete. Enjoy your binder!")
        elif status.status == "failed":
            line("🛑  Mission aborted. Check logs for clues.")
        else:
            line("✨  Stargazer is mapping protein space…")
        print(f"╚{bar}╝")
        if extra:
            print(extra)
            if not extra.endswith("\n"):
                print()

    def _clear(self) -> None:
        if _ipython_clear is not None:
            _ipython_clear(wait=True)
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

    @staticmethod
    def _format_message(message: str, width: int) -> str:
        notice = f"Message    : {message}"
        if len(notice) <= width:
            return notice
        truncated = notice[: max(0, width - 1)] + "…"
        return truncated


def monitor_job(
    client: BoltzFoldClient,
    job_id: str,
    *,
    poll_interval: float = 2.0,
    timeout: float | None = None,
    printer: LiveJobPrinter | None = None,
    summary_provider: Callable[[JobStatus], str | None] | None = None,
) -> JobStatus:
    """Stream job status updates until the job completes; returns the final status."""

    watcher = client.watch_job(job_id, poll_interval=poll_interval, timeout=timeout)
    printer = printer or LiveJobPrinter()
    start = time.perf_counter()
    last_status: JobStatus | None = None

    for status in watcher:
        last_status = status
        extra = summary_provider(status) if summary_provider else None
        printer.render(status, time.perf_counter() - start, extra=extra)

    if last_status is None:  # pragma: no cover - defensive
        last_status = client.fetch_status(job_id)
        extra = summary_provider(last_status) if summary_provider else None
        printer.render(last_status, time.perf_counter() - start, extra=extra)

    return last_status


@dataclass
class BulkJobPrinter:
    """Render progress for multiple jobs concurrently."""

    title: str = "BoltzFold Bulk Tracker"
    max_rows: int = 8
    auto_clear: bool = True

    def render(
        self,
        statuses: Mapping[str, JobStatus],
        job_names: Mapping[str, str],
        elapsed_seconds: float,
    ) -> None:
        if self.auto_clear:
            self._clear()

        width = max(60, min(120, _terminal_width()))
        bar = "═" * (width - 2)
        print(f"╔{bar}╗")
        self._line(width, f"✶ {self.title} ✶")
        print(f"╠{bar}╣")

        counts = Counter(status.status for status in statuses.values())
        summary = " | ".join(f"{key}:{counts.get(key, 0)}" for key in ("queued", "running", "succeeded", "failed"))
        self._line(width, f"Elapsed: {elapsed_seconds:6.1f}s   {summary}")
        print(f"╠{bar}╣")

        rows = list(statuses.items())
        rows.sort(key=lambda item: (item[1].status, job_names.get(item[0], item[0])))
        for job_id, status in rows[: self.max_rows]:
            name = job_names.get(job_id, job_id)
            msg = status.message or ""
            info = f"{status.status.upper():<9} {name} [{job_id}]"
            if msg:
                info = f"{info} :: {msg}"
            self._line(width, info)

        if len(rows) > self.max_rows:
            remaining = len(rows) - self.max_rows
            self._line(width, f"... plus {remaining} more")

        print(f"╚{bar}╝")

    @staticmethod
    def _line(width: int, text: str) -> None:
        inner = width - 4
        print(f"║ {text:<{inner}} ║")

    def _clear(self) -> None:
        if _ipython_clear is not None:
            _ipython_clear(wait=True)
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()


def monitor_jobs(
    client: BoltzFoldClient,
    jobs: Mapping[str, str] | Sequence[tuple[str, str]],
    *,
    poll_interval: float = 2.0,
    timeout: float | None = None,
    printer: BulkJobPrinter | None = None,
) -> Mapping[str, JobStatus]:
    """Track many jobs concurrently; returns a mapping of job_id -> final status."""

    if isinstance(jobs, Mapping):
        name_by_job = dict(jobs)
    else:
        name_by_job = {job_id: name for name, job_id in jobs}

    pending = dict(name_by_job)
    finished: dict[str, JobStatus] = {}
    printer = printer or BulkJobPrinter()
    start = time.perf_counter()
    deadline = start + timeout if timeout else None

    while pending:
        snapshot: dict[str, JobStatus] = {}
        for job_id in list(pending):
            status = client.fetch_status(job_id)
            snapshot[job_id] = status
            if status.status in {"succeeded", "failed"}:
                finished[job_id] = status
                pending.pop(job_id, None)
        printer.render(snapshot, name_by_job, time.perf_counter() - start)
        if pending:
            if deadline and time.perf_counter() >= deadline:
                break
            time.sleep(poll_interval)

    # Fetch final states for any jobs that exceeded timeout
    for job_id in pending:
        status = client.fetch_status(job_id)
        finished[job_id] = status

    return finished


# ---- summary helpers -------------------------------------------------------


def _summary_columns(include_job_url: bool) -> Sequence[tuple[str, Callable[[JobSummary], str]]]:
    columns: list[tuple[str, Callable[[JobSummary], str]]] = [
        ("NAME", lambda row: row.name),
        ("JOB ID", lambda row: row.job_id),
        ("STATUS", lambda row: row.status.upper()),
        ("PDB", lambda row: "yes" if row.pdb_url else ""),
        ("CIF", lambda row: "yes" if row.cif_url else ""),
    ]
    if include_job_url:
        columns.append(("JOB URL", lambda row: row.job_url or ""))
    return columns


def format_job_summary(
    rows: Sequence[JobSummary],
    *,
    include_job_url: bool = True,
) -> str:
    """Return a formatted table summarising job outcomes."""
    if not rows:
        return "\n(no jobs submitted yet)\n"

    columns = _summary_columns(include_job_url)
    widths = [len(label) for label, _ in columns]
    cells: list[list[str]] = []
    for row in rows:
        row_cells = [getter(row) for _, getter in columns]
        cells.append(row_cells)
        for idx, cell in enumerate(row_cells):
            widths[idx] = max(widths[idx], len(cell))

    def _fmt(values: Sequence[str]) -> str:
        padded = [f"{value:<{widths[idx]}}" for idx, value in enumerate(values)]
        return "  ".join(padded)

    header = _fmt([label for label, _ in columns])
    divider = "-" * len(header)
    body = "\n".join(_fmt(values) for values in cells)

    counts = Counter(row.status for row in rows)
    succeeded = sum(1 for row in rows if row.succeeded())
    summary_line = " | ".join(f"{name}:{counts.get(name, 0)}" for name in sorted(counts))
    completion = f"{succeeded}/{len(rows)} succeeded"

    parts = [
        "",
        f"Totals: {summary_line}  ({completion})",
        divider,
        header,
        divider,
        body,
        divider,
    ]
    return "\n".join(parts)


def print_job_summary(
    rows: Sequence[JobSummary],
    *,
    include_job_url: bool = True,
    stream: Any | None = None,
) -> None:
    """Print a formatted summary table to *stream* (defaults to stdout)."""
    text = format_job_summary(rows, include_job_url=include_job_url)
    sink = stream or sys.stdout
    sink.write(f"{text}\n")
