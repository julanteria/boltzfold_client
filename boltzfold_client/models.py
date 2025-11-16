"""Dataclasses describing BoltzFold request/response payloads."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PredictionPayload:
    """Structured representation of the JSON payload sent to `/v1/predict`."""

    model: str
    sequence: str
    raw: MutableMapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "model" not in self.raw:
            self.raw["model"] = self.model
        if "sequence" not in self.raw:
            self.raw["sequence"] = self.sequence

    def to_dict(self) -> dict[str, Any]:
        return dict(self.raw)


@dataclass(slots=True)
class PredictionResponse:
    job_id: str
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, payload: Mapping[str, Any]) -> PredictionResponse:
        return cls(job_id=str(payload["job_id"]), raw=payload)


@dataclass(slots=True)
class JobStatus:
    job_id: str
    status: str
    message: str | None = None
    pdb_url: str | None = None
    cif_url: str | None = None
    metrics_url: str | None = None
    job_url: str | None = None
    design_bundle_url: str | None = None
    cache_hit: bool | None = None
    worker_type: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, payload: Mapping[str, Any]) -> JobStatus:
        job_url = payload.get("job_url")
        if not job_url and payload.get("metrics_url"):
            metrics_url = str(payload.get("metrics_url"))
            job_url = metrics_url.replace("/files/", "/jobs/").rsplit("/", 1)[0]

        return cls(
            job_id=str(payload["job_id"]),
            status=str(payload["status"]),
            message=payload.get("message"),
            pdb_url=payload.get("pdb_url"),
            cif_url=payload.get("cif_url"),
            metrics_url=payload.get("metrics_url"),
            job_url=job_url,
            design_bundle_url=payload.get("design_bundle_url"),
            cache_hit=payload.get("cache_hit"),
            worker_type=payload.get("worker_type"),
            raw=payload,
        )

    def succeeded(self) -> bool:
        return self.status == "succeeded"

    def failed(self) -> bool:
        return self.status == "failed"


@dataclass(slots=True)
class JobSummary:
    """Lightweight snapshot for tabular reporting."""

    name: str
    job_id: str
    status: str
    message: str | None
    pdb_url: str | None
    cif_url: str | None
    metrics_url: str | None
    job_url: str | None

    @classmethod
    def from_status(cls, name: str, status: JobStatus) -> JobSummary:
        return cls(
            name=name,
            job_id=status.job_id,
            status=status.status,
            message=status.message,
            pdb_url=status.pdb_url,
            cif_url=status.cif_url,
            metrics_url=status.metrics_url,
            job_url=status.job_url,
        )

    def succeeded(self) -> bool:
        return self.status == "succeeded"

    def failed(self) -> bool:
        return self.status == "failed"
