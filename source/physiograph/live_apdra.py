"""Experimental live adaptation of APDRA's baseline-stability concept.

The frozen APDRA v0.7 remains in physiograph/apdra.py for retrospective
NASA OSD-575 laboratory analysis. This *separate* algorithm compares five
SIMULATED_LIVE vital channels against each subject's 45 valid rest samples,
summarized into three non-overlapping 15-sample reference blocks. The current
15-sample median is re-evaluated with one entire reference block omitted.

It is an exploratory software demonstration, NOT the validated laboratory
algorithm, an astronaut medical monitor, or a clinical threshold system.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
from statistics import median
from threading import RLock
from typing import Any

from .live_telemetry import LiveSample, METRICS, SOURCE

REFERENCE_POINTS = 45
BLOCK_POINTS = 15
WINDOW_POINTS = 15
PERIOD_SECONDS = 1.0
CHECK_SPACING_SECONDS = 15.0
# Research-only sensitivity settings chosen from ~1.5x the independent,
# pretrained five-channel model's physical normalization scales. No NASA
# reference ranges or clinical limits have been used to set them.
EXPLORATORY_DELTAS: dict[str, float] = {
    "heart_rate_bpm": 18.0,
    "spo2_percent": 3.0,
    "respiratory_rate_bpm": 6.0,
    "core_temp_c": 0.6,
    "hrv_rmssd_ms": 30.0,
}
assert set(EXPLORATORY_DELTAS) == set(METRICS)


def _reference_blocks(reference: list[dict[str, float]]) -> dict[str, list[float]]:
    if len(reference) != REFERENCE_POINTS:
        raise ValueError("Exactly 45 reference samples required")
    return {
        metric: [
            float(median(row[metric] for row in reference[start:start + BLOCK_POINTS]))
            for start in range(0, REFERENCE_POINTS, BLOCK_POINTS)
        ]
        for metric in METRICS
    }


def evaluate_window(
    reference: list[dict[str, float]], window: list[dict[str, float]]
) -> dict[str, Any]:
    """Deterministic per-channel leave-one-reference-BLOCK-out check.

    Using three block summaries avoids pretending 45 neighboring 1 Hz samples
    are 45 independent biological baselines. A deviation is "stable" only if
    all three leave-one-block-out checks exceed the research-only delta in
    the same direction. This is NOT a disease or risk classifier.
    """
    if len(window) != WINDOW_POINTS:
        raise ValueError("Exactly 15 recent samples required")
    if any(set(row) != set(METRICS) for row in reference + window):
        raise ValueError("Only complete five-channel simulated data may be compared")
    blocks = _reference_blocks(reference)
    channels = []
    stable, sensitive = [], []
    for key in METRICS:
        parts = blocks[key]
        full_baseline = float(median(parts))
        current = float(median(row[key] for row in window))
        limit = EXPLORATORY_DELTAS[key]
        leave_one_refs = [float(median(parts[:i] + parts[i + 1:])) for i in range(3)]
        deltas = [current - ref for ref in leave_one_refs]
        flags = [abs(d) >= limit for d in deltas]
        signs = [1 if d > 0 else -1 for d in deltas]
        consistent = all(flags) and len(set(signs)) == 1
        baseline_sensitive = any(flags) and not consistent
        classification = (
            "STABLE_DEVIATION" if consistent else
            "BASELINE_SENSITIVE" if baseline_sensitive else
            "NO_STABLE_DEVIATION"
        )
        if consistent:
            stable.append(key)
        elif baseline_sensitive:
            sensitive.append(key)
        channels.append({
            "key": key,
            "unit": METRICS[key][2],
            "baseline": round(full_baseline, 3),
            "recent": round(current, 3),
            "change": round(current - full_baseline, 3),
            "exploratory_delta": limit,
            "classification": classification,
            "direction": ("HIGHER" if current > full_baseline else "LOWER"
                          if current < full_baseline else "UNCHANGED"),
            "leave_one_block_flags": flags,
            "reference_block_medians": [round(value, 3) for value in parts],
        })
    return {
        "channels": channels,
        "stable_channels": stable,
        "baseline_sensitive_channels": sensitive,
        "status": ("STABLE_DEVIATION" if stable else
                   "BASELINE_SENSITIVE" if sensitive else "NO_STABLE_DEVIATION"),
    }


class LiveAPDRAMonitor:
    """Independent per-crew research screen, not the frozen NASA laboratory tool."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._states: dict[str, dict] = {}
        self._latest: dict[str, dict] = {}
        self._history: dict[str, deque] = {}

    def latest(self, subject_id: str) -> dict | None:
        with self._lock:
            return self._latest.get(subject_id)

    def history(self, subject_id: str, limit: int = 120) -> list[dict]:
        if not 1 <= limit <= 300:
            raise ValueError("History limit must be between 1 and 300")
        with self._lock:
            return list(self._history.get(subject_id, ())) [-limit:]

    def process(self, sample: LiveSample, quality: dict[str, Any]) -> dict[str, Any]:
        if sample.source != SOURCE:
            raise ValueError("Live APDRA accepts SIMULATED_LIVE only")
        if (quality.get("subject_id") != sample.subject_id
                or quality.get("sequence") != sample.sequence
                or quality.get("source") != SOURCE):
            raise ValueError("Live APDRA quality evidence must match the current packet")
        with self._lock:
            sid, seq = sample.subject_id, sample.sequence
            st = self._states.setdefault(sid, {
                "last_sequence": -1, "last_time": None,
                "reference": [], "window": deque(maxlen=WINDOW_POINTS),
                "last_confirmation": None, "confirmations": 0,
            })
            if seq <= st["last_sequence"]:
                raise ValueError("Live APDRA requires increasing packet sequence")
            gap = (
                st["last_time"] is not None
                and abs((sample.timestamp - st["last_time"]).total_seconds() - PERIOD_SECONDS) > .15
            )
            st["last_time"] = sample.timestamp
            st["last_sequence"] = seq
            activity = (sample.context or {}).get("activity_state", "UNKNOWN")
            result = {
                "subject_id": sid, "sequence": seq, "source": SOURCE,
                "algorithm": "APDRA_LIVE_BASELINE_STABILITY_EXPERIMENTAL",
                "algorithm_version": "live-v0.1",
                "historical_apdra_v07_modified": False,
                "nasa_laboratory_data_used": False,
                "input_channels": list(METRICS),
                "reference_points": len(st["reference"]),
                "reference_block_points": BLOCK_POINTS,
                "window_points": len(st["window"]),
                "activity_state": activity,
                "clinical_validation": False,
                "threshold_type": "EXPLORATORY_DELTA_NOT_MEDICAL_LIMIT",
                "explanation": ("Checks personal 15-sample medians against three "
                                "simulated baseline blocks, leaving one block out."),
                "limitation": ("Fictional streams only. Unvalidated adaptation of "
                               "APDRA's baseline-stability idea, not diagnosis "
                               "or a NASA operational limit."),
            }
            # Never interpret incomplete input, measurement-quality problems,
            # gaps, or uncertain/non-rest activity as a reliable deviation.
            if gap:
                st["window"].clear()
                if len(st["reference"]) < REFERENCE_POINTS:
                    st["reference"].clear()
                st["confirmations"] = 0
                st["last_confirmation"] = None
                result.update(status="IRREGULAR_CADENCE",
                              reason="Sampling gap: collect a clean window.")
            elif set(sample.values) != set(METRICS):
                st["window"].clear()
                st["confirmations"] = 0
                st["last_confirmation"] = None
                result.update(status="INCOMPLETE_METRICS",
                              reason="Five complete physiological values are required.")
            elif quality.get("status") != "NO_QUALITY_ISSUE_DETECTED":
                st["window"].clear()
                st["confirmations"] = 0
                st["last_confirmation"] = None
                result.update(status="VERIFY_MEASUREMENT_QUALITY",
                              reason="Check simulated signal quality before baseline comparison.")
            elif activity != "REST":
                st["window"].clear()
                st["confirmations"] = 0
                st["last_confirmation"] = None
                result.update(status="ACTIVITY_CONTEXT",
                              reason="Baseline checks use rest-declared samples only.")
            elif len(st["reference"]) < REFERENCE_POINTS:
                st["reference"].append(dict(sample.values))
                result.update(status="BASELINE_CALIBRATING",
                              progress=len(st["reference"]),
                              required=REFERENCE_POINTS,
                              reason="Collecting 45 simulated readings during declared rest.")
            else:
                st["window"].append(dict(sample.values))
                if len(st["window"]) < WINDOW_POINTS:
                    result.update(status="WINDOW_COLLECTING",
                                  progress=len(st["window"]), required=WINDOW_POINTS,
                                  reason="Collecting 15 recent rest-declared readings.")
                else:
                    assessment = evaluate_window(st["reference"], list(st["window"]))
                    result.update(assessment)
                    if assessment["stable_channels"]:
                        now: datetime = sample.timestamp
                        previous: datetime | None = st["last_confirmation"]
                        if previous is None or (now - previous).total_seconds() >= CHECK_SPACING_SECONDS:
                            st["confirmations"] += 1
                            st["last_confirmation"] = now
                    else:
                        st["confirmations"] = 0
                        st["last_confirmation"] = None
                    result["spaced_confirmations"] = st["confirmations"]
                    result["persistence_confirmed"] = st["confirmations"] >= 2
                    result["reason"] = {
                        "STABLE_DEVIATION": "A personal-baseline change remains flagged across all three reference checks.",
                        "BASELINE_SENSITIVE": "At least one reference check changes the result. Review the baseline.",
                        "NO_STABLE_DEVIATION": "No channel crosses the exploratory delta in every reference check.",
                    }[assessment["status"]]
            result["reference_points"] = len(st["reference"])
            result["window_points"] = len(st["window"])
            self._latest[sid] = result
            self._history.setdefault(sid, deque(maxlen=300)).append(result)
            return result
