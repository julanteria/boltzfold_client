"""Unit tests for the lightweight BoltzFold client helpers."""

from __future__ import annotations

import types
from typing import Any

import pytest

from boltzfold_client import (
    BoltzFoldClient,
    BulkJobPrinter,
    chunked,
    iter_fasta,
    load_first_sequence,
    monitor_jobs,
)
from boltzfold_client.models import JobStatus, PredictionResponse


class _DummyHTTPClient:
    def close(self) -> None:  # pragma: no cover - noop
        pass


def test_build_payload_with_binder_and_target_strings() -> None:
    client = BoltzFoldClient(base_url="http://example.com", client=_DummyHTTPClient())

    payload = client.build_payload(
        model="boltz",
        sequence="ACDE",
        binder_sequence="acde",
        target_sequence="wxyz",
    )

    assert payload.raw["binder_sequence"] == "ACDE"
    assert payload.raw["target_sequence"] == "WXYZ"


def test_build_payload_reads_sequences_from_paths(tmp_path) -> None:
    binder_path = tmp_path / "binder.fa"
    binder_path.write_text(">binder\nacde\n>ignored\nZZZZ\n", encoding="utf-8")
    target_path = tmp_path / "target.fa"
    target_path.write_text(">target\nwxyz", encoding="utf-8")

    client = BoltzFoldClient(base_url="http://example.com", client=_DummyHTTPClient())
    payload = client.build_payload(
        model="boltz",
        sequence="ACDE",
        binder_sequence_path=binder_path,
        target_sequence_path=target_path,
    )

    assert payload.raw["binder_sequence"] == "ACDE"
    assert payload.raw["target_sequence"] == "WXYZ"


def test_build_payload_rejects_duplicate_sequence_sources(tmp_path) -> None:
    binder_path = tmp_path / "binder.fa"
    binder_path.write_text("ACDE", encoding="utf-8")

    client = BoltzFoldClient(base_url="http://example.com", client=_DummyHTTPClient())

    with pytest.raises(ValueError):
        client.build_payload(
            model="boltz",
            sequence="ACDE",
            binder_sequence="ACDE",
            binder_sequence_path=binder_path,
        )


def test_submit_binder_target_prediction_sets_defaults() -> None:
    client = BoltzFoldClient(base_url="http://example.com", client=_DummyHTTPClient())
    captured: dict[str, object] = {}

    def _fake_submit(self, **params):
        captured.update(params)
        return PredictionResponse(job_id="abc123", raw={})

    client.submit_prediction = types.MethodType(_fake_submit, client)
    response = client.submit_binder_target_prediction(
        binder_sequence="ACDE",
        target_sequence="WXYZ",
        extra={"job_name": "binder-1"},
    )

    assert isinstance(response, PredictionResponse)
    assert captured["model"] == "boltz"
    assert captured["sequence"] == "ACDE"
    assert captured["binder_sequence"] == "ACDE"
    assert captured["target_sequence"] == "WXYZ"
    assert captured["extra"] == {"job_name": "binder-1"}


def test_submit_bulk_predictions(monkeypatch) -> None:
    client = BoltzFoldClient(base_url="http://example.com", client=_DummyHTTPClient())
    calls: list[dict[str, Any]] = []

    def _fake_submit(self, **params):
        calls.append(params)
        return PredictionResponse(job_id=str(len(calls)), raw={})

    client.submit_prediction = types.MethodType(_fake_submit, client)
    responses = client.submit_bulk_predictions(
        [
            {"model": "boltz", "sequence": "AAAA"},
            {"model": "openfold3", "sequence": "BBBB"},
        ]
    )

    assert len(responses) == 2
    assert calls[0]["sequence"] == "AAAA"
    assert calls[1]["model"] == "openfold3"


def test_submit_binder_target_batch(monkeypatch) -> None:
    client = BoltzFoldClient(base_url="http://example.com", client=_DummyHTTPClient())
    calls: list[dict[str, Any]] = []

    def _fake_submit(self, **params):
        calls.append(params)
        return PredictionResponse(job_id=str(len(calls)), raw={})

    client.submit_binder_target_prediction = types.MethodType(_fake_submit, client)
    jobs = [
        {"binder_sequence": "AAAA", "target_sequence": "TTTT", "extra": {"job_name": "one"}},
        {"binder_sequence": "CCCC", "target_sequence": "GGGG", "extra": {"job_name": "two"}},
    ]
    responses = client.submit_binder_target_batch(jobs, seed=42)

    assert len(responses) == 2
    assert calls[0]["seed"] == 42
    assert calls[1]["extra"]["job_name"] == "two"


def test_load_first_sequence_reads_plain_and_fasta(tmp_path) -> None:
    fasta = tmp_path / "seq.fa"
    fasta.write_text(">foo\nacde\n>bar\nzzzz\n", encoding="utf-8")
    assert load_first_sequence(fasta) == "ACDE"

    plain = tmp_path / "seq.txt"
    plain.write_text(" wxyz ", encoding="utf-8")
    assert load_first_sequence(plain) == "WXYZ"


def test_iter_fasta_and_chunked_helpers(tmp_path) -> None:
    fasta = tmp_path / "designs.fa"
    fasta.write_text(">a\nac\n>b\nzz\n>c\nyy\n", encoding="utf-8")

    sequences = list(iter_fasta(fasta))
    assert sequences == [("a", "AC"), ("b", "ZZ"), ("c", "YY")]

    chunks = list(chunked(sequences, size=2))
    assert len(chunks) == 2
    assert chunks[0] == [("a", "AC"), ("b", "ZZ")]
    assert chunks[1] == [("c", "YY")]

    with pytest.raises(ValueError):
        list(chunked(sequences, size=0))


def test_monitor_jobs_tracks_multiple_jobs(monkeypatch) -> None:
    statuses = {
        "job1": [
            JobStatus(job_id="job1", status="running"),
            JobStatus(job_id="job1", status="succeeded", pdb_url="pdb1"),
        ],
        "job2": [
            JobStatus(job_id="job2", status="queued"),
            JobStatus(job_id="job2", status="running"),
            JobStatus(job_id="job2", status="failed", message="boom"),
        ],
    }

    class _StubClient:
        def __init__(self):
            self.calls: dict[str, int] = {}

        def fetch_status(self, job_id: str) -> JobStatus:
            idx = self.calls.get(job_id, 0)
            seq = statuses[job_id]
            self.calls[job_id] = idx + 1
            return seq[min(idx, len(seq) - 1)]

    client = _StubClient()
    printer = BulkJobPrinter(auto_clear=False, max_rows=4)
    result = monitor_jobs(client, {"job1": "alpha", "job2": "beta"}, poll_interval=0.0, printer=printer)

    assert result["job1"].status == "succeeded"
    assert result["job2"].status == "failed"
