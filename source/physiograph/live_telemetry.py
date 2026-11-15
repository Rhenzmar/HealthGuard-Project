"""PhysioGraph v1.0: source-aware live *demonstration* telemetry ingestion.

This module deliberately does not interpret physiological measurements as normal,
abnormal, or diagnostic. It is a bounded, in-memory transport/quality layer.
Historical OSD-575 APDRA data are never modified or merged with these packets.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from threading import RLock
from typing import Any
import re

# Physical plausibility limits are input-integrity guardrails only, NOT medical
# thresholds or safety limits. Units are encoded in the canonical field names.
METRICS: dict[str, tuple[float, float, str]] = {
    "heart_rate_bpm": (20.0, 250.0, "bpm"),
    "spo2_percent": (50.0, 100.0, "%"),
    "respiratory_rate_bpm": (4.0, 70.0, "breaths/min"),
    "core_temp_c": (30.0, 43.0, "°C"),
    "hrv_rmssd_ms": (0.0, 400.0, "ms"),
}
SOURCE = "SIMULATED_LIVE"
ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,32}\Z")
ACTIVITY_STATES = frozenset({'REST', 'ACTIVE', 'UNKNOWN'})
CONTEXT_BASES = frozenset({'SIMULATOR_DECLARED', 'OPERATOR_DECLARED'})


class TelemetryError(ValueError):
    """Invalid, ambiguous, or unsupported telemetry packet."""


class ConflictError(TelemetryError):
    """A sequence number, timepoint, or subject cannot be accepted."""


@dataclass(frozen=True)
class LiveSample:
    subject_id: str
    sequence: int
    timestamp: datetime
    values: dict[str, float]
    source: str = SOURCE
    context: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "values": dict(self.values),
            "source": self.source,
            "context": dict(self.context) if self.context is not None else None,
            "analysis_status": "NOT_EVALUATED",  # no APDRA/ML/medical inference
        }


def validate_sample(payload: dict[str, Any]) -> LiveSample:
    """Strict schema; no inferred units, forward-filling, or provenance claims."""
    expected = {"subject_id", "sequence", "timestamp", "values", "source"}
    if not isinstance(payload, dict) or set(payload) not in (expected, expected | {'context'}):
        raise TelemetryError(f"Packet must have exactly {sorted(expected)} with optional context")
    subject = payload["subject_id"]
    if not isinstance(subject, str) or not ID_PATTERN.fullmatch(subject):
        raise TelemetryError("subject_id must be a pseudonymous ASCII code, 1-32 characters")
    if payload["source"] != SOURCE:
        raise TelemetryError("Only SIMULATED_LIVE packets are supported; never label these NASA data")
    seq = payload["sequence"]
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
        raise TelemetryError("sequence must be a nonnegative integer")
    raw_time = payload["timestamp"]
    if not isinstance(raw_time, str):
        raise TelemetryError("timestamp must be an ISO-8601 timezone-aware string")
    try:
        stamp = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    except ValueError as e:
        raise TelemetryError("Invalid timestamp") from e
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise TelemetryError("Timestamp must contain timezone information")
    stamp = stamp.astimezone(timezone.utc)
    values = payload["values"]
    if not isinstance(values, dict) or not 1 <= len(values) <= len(METRICS):
        raise TelemetryError("values must contain 1-5 explicitly named physiological measurements")
    clean = {}
    for k,v in values.items():
        if k not in METRICS:
            raise TelemetryError(f"Unknown metric {k!r}; no unit conversion is inferred")
        if isinstance(v, bool) or not isinstance(v, (float,int)) or not isfinite(v):
            raise TelemetryError(f"{k} must be a finite numeric measurement")
        lo, hi, _ = METRICS[k]
        if not (lo <= v <= hi):
            raise TelemetryError(f"{k} outside broad technical validation range [{lo}, {hi}]")
        clean[k] = float(v)
    context = payload.get('context')
    if context is not None:
        if not isinstance(context, dict) or set(context) != {'activity_state', 'basis'}:
            raise TelemetryError('context must have exactly activity_state and basis')
        if context['activity_state'] not in ACTIVITY_STATES or context['basis'] not in CONTEXT_BASES:
            raise TelemetryError('Invalid activity_state or context basis; not a measured diagnosis')
        context = dict(context)
    return LiveSample(subject, seq, stamp, clean, context=context)


class LiveStore:
    """Thread-safe in-memory buffer with strict per-subject ordering.

    This is intentionally ephemeral. It is not a medical record repository.
    """
    def __init__(self, *, max_per_subject: int = 600, max_subjects: int = 8):
        if max_per_subject < 1 or max_subjects < 1:
            raise ValueError("Positive buffer limits are required")
        self.max_per_subject = max_per_subject
        self.max_subjects = max_subjects
        self._samples: dict[str, deque[LiveSample]] = {}
        self._last: dict[str, tuple[int, datetime]] = {}
        self._lock = RLock()

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        sample = validate_sample(payload)
        with self._lock:
            last = self._last.get(sample.subject_id)
            if last is not None and sample.sequence <= last[0]:
                raise ConflictError("Sequence must be strictly increasing for each subject")
            if last is not None and sample.timestamp <= last[1]:
                raise ConflictError("Timestamp must be strictly increasing for each subject")
            if sample.subject_id not in self._samples:
                if len(self._samples) >= self.max_subjects:
                    raise ConflictError("Maximum demonstration subject count reached")
                self._samples[sample.subject_id] = deque(maxlen=self.max_per_subject)
            self._samples[sample.subject_id].append(sample)
            self._last[sample.subject_id] = (sample.sequence, sample.timestamp)
            return {"accepted":True, "packet":sample.as_dict(), "retained":len(self._samples[sample.subject_id])}

    def get_last_sample(self, subject_id: str) -> LiveSample:
        """Return the typed packet just accepted, without changing its meaning."""
        with self._lock:
            q=self._samples.get(subject_id)
            if not q:
                raise TelemetryError("No sample has been accepted for this subject")
            return q[-1]

    def subjects(self) -> list[str]:
        with self._lock:
            return sorted(self._samples)

    def history(self, subject_id: str, *, limit: int = 120) -> list[dict[str, Any]]:
        if not ID_PATTERN.fullmatch(subject_id):
            raise TelemetryError("Invalid subject_id")
        if not 1 <= limit <= self.max_per_subject:
            raise TelemetryError(f"limit must be between 1 and {self.max_per_subject}")
        with self._lock:
            return [s.as_dict() for s in list(self._samples.get(subject_id, ())) [-limit:]]

    def latest(self, subject_id: str) -> dict[str, Any] | None:
        with self._lock:
            queue = self._samples.get(subject_id)
            return queue[-1].as_dict() if queue else None

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "mode": "SIMULATION_ONLY", "analysis_status": "NOT_EVALUATED",
                "subject_count": len(self._samples),
                "subjects": {k: {"latest": v[-1].as_dict(), "retained": len(v)}
                             for k,v in self._samples.items() if v},
            }

    def reset(self) -> None:
        """For isolated tests or manually restarted demos, never hidden auto-reset."""
        with self._lock:
            self._samples.clear()
            self._last.clear()
