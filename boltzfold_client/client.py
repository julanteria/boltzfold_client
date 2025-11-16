"""Simple HTTPX-based clients for the BoltzFold API."""

from __future__ import annotations

import asyncio
import base64
import time
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from .models import JobStatus, PredictionPayload, PredictionResponse

DEFAULT_BASE_URL = "https://boltzfold.com"


def _encode_target_file(path: Path) -> tuple[str, str]:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return path.name, data


def _normalize_sequence_text(value: str, *, label: str) -> str:
    cleaned = "".join(value.split()).upper()
    if not cleaned:
        raise ValueError(f"{label} sequence is empty")
    return cleaned


def _load_sequence_from_path(path: Path, *, label: str) -> str:
    material = path.read_text().splitlines()
    seq: list[str] = []
    for raw in material:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if seq:
                break
            continue
        seq.append(line)
    if not seq:
        raise ValueError(f"{label} sequence file {path} contained no residues")
    return _normalize_sequence_text("".join(seq), label=label)


def _resolve_sequence_field(
    *,
    label: str,
    inline_value: str | None,
    path_value: str | Path | None,
) -> str | None:
    if inline_value and path_value:
        raise ValueError(f"{label} sequence supplied both inline and via path")
    if path_value is not None:
        resolved = Path(path_value).expanduser().resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"{label} sequence file not found: {resolved}")
        return _load_sequence_from_path(resolved, label=label)
    if inline_value:
        return _normalize_sequence_text(inline_value, label=label)
    return None


def _normalize_length(length: str | tuple[int, int] | Iterable[int] | None) -> str | None:
    if length is None:
        return None
    if isinstance(length, str):
        cleaned = length.strip()
        return cleaned or None
    if isinstance(length, tuple):
        if len(length) != 2:
            raise ValueError("length tuple must contain two integers")
        lo, hi = length
        if lo > hi:
            lo, hi = hi, lo
        return f"{lo}-{hi}"
    try:
        seq = list(length)
    except TypeError as exc:  # pragma: no cover - defensive
        raise ValueError("length iterable must be a sequence of two integers") from exc
    if len(seq) != 2:
        raise ValueError("length iterable must contain two integers")
    lo, hi = int(seq[0]), int(seq[1])
    if lo > hi:
        lo, hi = hi, lo
    return f"{lo}-{hi}"


def _merge_extra(payload: MutableMapping[str, Any], extra: Mapping[str, Any] | None) -> None:
    if extra:
        for key, value in extra.items():
            if value is not None:
                payload[key] = value


def _create_payload(
    *,
    model: str,
    sequence: str,
    target_file_path: str | Path | None = None,
    target_url: str | None = None,
    length: str | tuple[int, int] | Iterable[int] | None = None,
    epitope: Mapping[str, Any] | None = None,
    num_designs: int | None = None,
    openfold_chains: Iterable[Mapping[str, Any]] | None = None,
    binder_sequence: str | None = None,
    binder_sequence_path: str | Path | None = None,
    target_sequence: str | None = None,
    target_sequence_path: str | Path | None = None,
    extra: Mapping[str, Any] | None = None,
) -> PredictionPayload:
    payload: MutableMapping[str, Any] = {"model": model, "sequence": sequence}

    if target_url:
        payload["target_file"] = target_url

    if target_file_path:
        path = Path(target_file_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Target structure not found: {path}")
        filename, encoded = _encode_target_file(path)
        payload["target_file_name"] = filename
        payload["target_file_data"] = encoded

    length_spec = _normalize_length(length)
    if length_spec:
        payload["length"] = length_spec

    if epitope:
        payload["epitope"] = dict(epitope)

    if num_designs is not None:
        payload["num_designs"] = num_designs

    if openfold_chains:
        payload["openfold_chains"] = [dict(chain) for chain in openfold_chains]

    binder_value = _resolve_sequence_field(
        label="binder",
        inline_value=binder_sequence,
        path_value=binder_sequence_path,
    )
    if binder_value:
        payload["binder_sequence"] = binder_value

    target_value = _resolve_sequence_field(
        label="target",
        inline_value=target_sequence,
        path_value=target_sequence_path,
    )
    if target_value:
        payload["target_sequence"] = target_value

    _merge_extra(payload, extra)
    return PredictionPayload(model=model, sequence=sequence, raw=payload)


@dataclass(slots=True)
class JobWatcher:
    """Iterator that polls job status until completion."""

    client: BoltzFoldClient
    job_id: str
    poll_interval: float = 1.0
    timeout: float | None = None

    def __iter__(self):
        deadline = time.perf_counter() + self.timeout if self.timeout else None
        while True:
            status = self.client.fetch_status(self.job_id)
            yield status
            if status.status in {"succeeded", "failed"}:
                break
            if deadline and time.perf_counter() >= deadline:
                break
            time.sleep(self.poll_interval)


class BoltzFoldClient:
    """Small synchronous wrapper around the `/v1/predict` and `/v1/jobs/{id}` endpoints."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        request_timeout: float = 30.0,
        read_timeout: float = 300.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=httpx.Timeout(request_timeout, read=read_timeout))
        self._owns_client = client is None

    # ---- payload helpers -------------------------------------------------

    def build_payload(
        self,
        *,
        model: str,
        sequence: str,
        target_file_path: str | Path | None = None,
        target_url: str | None = None,
        length: str | tuple[int, int] | Iterable[int] | None = None,
        epitope: Mapping[str, Any] | None = None,
        num_designs: int | None = None,
        openfold_chains: Iterable[Mapping[str, Any]] | None = None,
        binder_sequence: str | None = None,
        binder_sequence_path: str | Path | None = None,
        target_sequence: str | None = None,
        target_sequence_path: str | Path | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> PredictionPayload:
        return _create_payload(
            model=model,
            sequence=sequence,
            target_file_path=target_file_path,
            target_url=target_url,
            length=length,
            epitope=epitope,
            num_designs=num_designs,
            openfold_chains=openfold_chains,
            binder_sequence=binder_sequence,
            binder_sequence_path=binder_sequence_path,
            target_sequence=target_sequence,
            target_sequence_path=target_sequence_path,
            extra=extra,
        )

    # ---- HTTP calls ------------------------------------------------------

    def submit_prediction(self, **params: Any) -> PredictionResponse:
        payload = self.build_payload(**params)
        url = f"{self.base_url}/v1/predict"
        response = self._client.post(url, json=payload.to_dict())
        response.raise_for_status()
        return PredictionResponse.from_response(response.json())

    def submit_bulk_predictions(self, payloads: Sequence[Mapping[str, Any]]) -> Sequence[PredictionResponse]:
        """Submit multiple prediction payloads sequentially."""
        responses: list[PredictionResponse] = []
        for payload in payloads:
            responses.append(self.submit_prediction(**dict(payload)))
        return responses

    def submit_binder_target_prediction(
        self,
        *,
        binder_sequence: str | None = None,
        binder_sequence_path: str | Path | None = None,
        target_sequence: str | None = None,
        target_sequence_path: str | Path | None = None,
        extra: Mapping[str, Any] | None = None,
        **params: Any,
    ) -> PredictionResponse:
        binder = _resolve_sequence_field(
            label="binder",
            inline_value=binder_sequence,
            path_value=binder_sequence_path,
        )
        target = _resolve_sequence_field(
            label="target",
            inline_value=target_sequence,
            path_value=target_sequence_path,
        )
        if binder is None:
            raise ValueError("binder sequence is required for binder/target predictions")
        if target is None:
            raise ValueError("target sequence is required for binder/target predictions")

        merged_params = dict(params)
        merged_params.setdefault("model", "boltz")
        merged_params.setdefault("sequence", binder)

        return self.submit_prediction(
            binder_sequence=binder,
            target_sequence=target,
            extra=extra,
            **merged_params,
        )

    def submit_binder_target_batch(
        self,
        jobs: Sequence[Mapping[str, Any]],
        **common_params: Any,
    ) -> Sequence[PredictionResponse]:
        """Submit many binder/target jobs in one call."""
        responses: list[PredictionResponse] = []
        for job in jobs:
            merged = dict(common_params)
            merged.update(job)
            responses.append(self.submit_binder_target_prediction(**merged))
        return responses

    def fetch_status(self, job_id: str) -> JobStatus:
        url = f"{self.base_url}/v1/jobs/{job_id}"
        response = self._client.get(url)
        response.raise_for_status()
        return JobStatus.from_response(response.json())

    def watch_job(
        self,
        job_id: str,
        *,
        poll_interval: float = 5.0,
        timeout: float | None = None,
    ) -> JobWatcher:
        return JobWatcher(self, job_id, poll_interval=poll_interval, timeout=timeout)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def job_url(self, job_id: str) -> str:
        return f"{self.base_url}/jobs/{job_id}"

    def __enter__(self) -> BoltzFoldClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class AsyncBoltzFoldClient:
    """Async variant backed by `httpx.AsyncClient`."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        request_timeout: float = 30.0,
        read_timeout: float = 300.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(request_timeout, read=read_timeout))
        self._owns_client = client is None

    async def submit_prediction(self, **params: Any) -> PredictionResponse:
        payload = _create_payload(**params)
        url = f"{self.base_url}/v1/predict"
        response = await self._client.post(url, json=payload.to_dict())
        response.raise_for_status()
        return PredictionResponse.from_response(response.json())

    async def fetch_status(self, job_id: str) -> JobStatus:
        url = f"{self.base_url}/v1/jobs/{job_id}"
        response = await self._client.get(url)
        response.raise_for_status()
        return JobStatus.from_response(response.json())

    async def watch_job(
        self,
        job_id: str,
        *,
        poll_interval: float = 5.0,
        timeout: float | None = None,
    ):
        deadline = time.perf_counter() + timeout if timeout else None
        while True:
            status = await self.fetch_status(job_id)
            yield status
            if status.status in {"succeeded", "failed"}:
                break
            if deadline and time.perf_counter() >= deadline:
                break
            await asyncio.sleep(poll_interval)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncBoltzFoldClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()
