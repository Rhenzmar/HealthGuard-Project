"""Unified HealthGuard PhysioAlert training review for fictional telemetry.

Combines existing fixed five-channel evidence with a separate experimental
17-channel model and synthetic engineering departures. Labels are scripted
training attention levels, NOT health states, medical triage or NASA limits.
Never silently interprets reconstruction error as a clinical risk score.
"""
from __future__ import annotations

from collections import deque
from threading import RLock
from typing import Any

from .live_telemetry import SOURCE
from .engineering_sim import ENGINEERING_SOURCE, SIGNALS

LEVELS = ("OPTIMAL", "CHECK", "WARNING", "CRITICAL")
READY = {"MODEL_FLAG", "NO_MODEL_FLAG"}

# Selected generic training guidance; only operator-authorized checklist actions,
# no automated treatment, diagnosis, or invalid spacecraft operations.
GUIDANCE = {
    "OPTIMAL": ("The simulated measurements currently show no flagged engineering deviation "
                "and no flagged experimental model pattern. Continue monitoring. "
                "This does not establish that an astronaut is medically healthy."),
    "CHECK": ("Check the simulated measurements and their timestamps. Confirm signal quality, "
              "activity context, and any model disagreement before interpreting a change."),
    "WARNING": ("Training warning: a numerical deviation or experimental pattern needs review. "
                "Verify the applicable instrument and follow the approved mission checklist. "
                "Notify the responsible crew member and Mission Control as appropriate."),
    "CRITICAL": ("Critical training scenario: a simulated engineering channel has crossed its "
                 "predefined demonstration deviation threshold. Alert the crew and follow "
                 "approved mission response procedures. This is not a validated safety limit "
                 "or a medical emergency diagnosis."),
}


def _assert_matching(subject_id: str, sequence: int, item: dict, name: str) -> None:
    if not isinstance(item, dict) or item.get("subject_id") != subject_id or item.get("sequence") != sequence:
        raise ValueError(f"{name} evidence does not match the selected crew packet")


def compose_review(subject_id: str, sequence: int, physiological_packet: dict,
                   cnn: dict, comparison: dict, context: dict,
                   candidate: dict, engineering: dict, apdra: dict | None = None) -> dict[str, Any]:
    """Return evidence-based attention levels, not model-predicted illness."""
    if physiological_packet.get("subject_id") != subject_id or physiological_packet.get("sequence") != sequence:
        raise ValueError("Physiological packet subject/sequence mismatch")
    if physiological_packet.get("source") != SOURCE:
        raise ValueError("Physiological stream must have simulated provenance")
    for name, element in (("legacy_cnn",cnn),("statistical_comparator",comparison),
                          ("context",context),("candidate17",candidate),("engineering",engineering)):
        _assert_matching(subject_id, sequence, element, name)
    if any(element.get("source") != SOURCE for element in (cnn,comparison,context)):
        raise ValueError("Legacy model/context source mismatch")
    if engineering.get("source") != ENGINEERING_SOURCE:
        raise ValueError("Engineering simulation provenance mismatch")
    if candidate.get("source") != "FULLY_SYNTHETIC_17_CHANNELS":
        raise ValueError("17-channel model must retain synthetic-only provenance")
    if candidate.get("NASA_laboratory_data_used") is not False:
        raise ValueError("Candidate cannot claim historical NASA laboratory inference")

    if apdra is not None:
        _assert_matching(subject_id, sequence, apdra, "live_apdra")
        if (apdra.get("source") != SOURCE
                or apdra.get("algorithm") != "APDRA_LIVE_BASELINE_STABILITY_EXPERIMENTAL"
                or apdra.get("nasa_laboratory_data_used") is not False):
            raise ValueError("Live APDRA must be experimental, simulated and source-isolated")

    candidate_status = candidate.get("status", "MODEL_UNAVAILABLE")
    old_a,old_b = cnn.get("status"),comparison.get("status")
    both_legacy_ready = old_a in READY and old_b in READY
    both_legacy_flagged = old_a == "MODEL_FLAG" and old_b == "MODEL_FLAG"
    candidate_ready = candidate_status in READY
    candidate_flagged = candidate_status == "MODEL_FLAG"
    quality = context.get("quality") or {}
    quality_issue = quality.get("status") != "NO_QUALITY_ISSUE_DETECTED"
    observation_context = context.get("status")
    engineering_tier = engineering.get("status")
    if engineering_tier not in LEVELS or set(engineering.get("channels", {})) != set(SIGNALS):
        raise ValueError("Invalid engineering evidence schema")
    if any(channel.get("source") != ENGINEERING_SOURCE for channel in engineering["channels"].values()):
        raise ValueError("Engineering channel origin mismatch")

    # Model-based agreement can escalate attention at most to WARNING, never
    # an emergency. Quality concern forces model evidence to abstain.
    model_tier = "CHECK"
    if quality_issue:
        model_reason = "Signal integrity or cadence requires verification before interpreting model flags."
    elif not (candidate_ready and both_legacy_ready):
        model_reason = "One or more trained detectors are still warming up or unavailable."
    elif candidate_flagged and both_legacy_flagged and observation_context in (
        "PERSISTENT_PATTERN_REVIEW", "OBSERVE_UNUSUAL_PATTERN", "ACTIVITY_CONTEXT_REVIEW",
        "ACTIVITY_CONTEXT_UNKNOWN", "POST_ACTIVITY_OBSERVATION"
    ):
        model_tier = "WARNING"
        model_reason = "The experimental 17-channel model and both original detectors flag a numerical pattern. Confirm context and measurements."
    elif candidate_flagged or old_a == "MODEL_FLAG" or old_b == "MODEL_FLAG":
        model_tier = "CHECK"
        model_reason = "A detector flagged the simulated pattern, but the combined evidence is incomplete or not fully corroborated."
    else:
        model_tier = "OPTIMAL"
        model_reason = "The available models do not flag this simulated window; this does not establish astronaut health."

    # APDRA adds independent evidence for a cautious measurement CHECK only.
    # It cannot cause a training WARNING/CRITICAL, or reduce existing severity.
    apdra_check = bool(
        apdra is not None and
        apdra.get("status") == "STABLE_DEVIATION" and
        apdra.get("persistence_confirmed") is True and
        not quality_issue and
        context.get("activity_state") == "REST"
    )
    if apdra_check and model_tier == "OPTIMAL":
        model_tier = "CHECK"
        model_reason = ("The experimental live APDRA check found a persistent "
                        "personal-baseline change. Verify the simulated measurements.")

    # CRITICAL is possible only through clearly labelled engineering demo
    # heuristics, never by an AI score or human vital sign alone.
    peak = LEVELS[max(LEVELS.index(model_tier), LEVELS.index(engineering_tier))]
    if LEVELS.index(engineering_tier) > LEVELS.index(model_tier):
        reason = ("Fictional engineering value(s) departed from predefined simulator "
                  "reference values; these are not mission safety or medical limits.")
        basis = "SIMULATED_ENGINEERING_THRESHOLD"
    else:
        reason = model_reason
        basis = "EXPERIMENTAL_MODEL_AGREEMENT_OR_DATA_QUALITY"

    flagged = [key for key in engineering.get("flagged_channels", []) if key in SIGNALS]
    residuals = candidate.get("largest_reconstruction_errors") or []
    # Residuals are only meaningful if the 17-channel model has scored a window.
    residuals = [
        {"channel": item["channel"], "error": item["error"]}
        for item in residuals
        if candidate_ready and item.get("channel") in set(SIGNALS) | set(physiological_packet["values"])
           and isinstance(item.get("error"), (int,float))
    ][:5]
    details = {
        "candidate_17ch": {
            "status": candidate_status,
            "model_version": candidate.get("model_version"),
            "reconstruction_error": candidate.get("reconstruction_error"),
            "calibration_threshold": candidate.get("threshold"),
            "physiological_error": candidate.get("physiological_error"),
            "engineering_error": candidate.get("engineering_error"),
            "top_reconstruction_residuals": residuals,
            "classification": "EXPERIMENTAL_NOVELTY_ONLY",
        },
        "five_channel_cnn": {"status": old_a, "score": cnn.get("reconstruction_error")},
        "statistical_comparator": {"status": old_b, "score": comparison.get("novelty_score")},
        "context": {"status": observation_context,
                    "activity_state": context.get("activity_state"),
                    "measurement_quality": quality.get("status"),
                    "quality_issues": quality.get("issues", [])},
        "apdra_live": {
            "status": apdra.get("status") if apdra else "NOT_AVAILABLE",
            "version": apdra.get("algorithm_version") if apdra else None,
            "reference_points": apdra.get("reference_points", 0) if apdra else 0,
            "window_points": apdra.get("window_points", 0) if apdra else 0,
            "reason": apdra.get("reason") if apdra else None,
            "stable_channels": apdra.get("stable_channels", []) if apdra else [],
            "baseline_sensitive_channels": apdra.get("baseline_sensitive_channels", []) if apdra else [],
            "channels": apdra.get("channels", []) if apdra else [],
            "spaced_confirmations": apdra.get("spaced_confirmations", 0) if apdra else 0,
            "persistence_confirmed": apdra.get("persistence_confirmed", False) if apdra else False,
            "contributed_check": apdra_check,
            "classification": "EXPERIMENTAL_SIMULATED_BASELINE_STABILITY_ONLY",
        },
        "engineering": {
            "status": engineering_tier, "flagged_channels": flagged,
            "channels": [
                {"key": key, "status": engineering["channels"][key]["status"],
                 "value": engineering["channels"][key]["value"],
                 "unit": engineering["channels"][key]["unit"]}
                for key in flagged
            ],
            "classification_method": "SIMULATED_REFERENCE_DELTA_ONLY"
        }
    }
    return {
        "subject_id": subject_id, "sequence": sequence,
        "source": "SIMULATED_PHYSIOALERT_COMBINED",
        "source_components": [SOURCE, ENGINEERING_SOURCE, "FULLY_SYNTHETIC_17_CHANNELS"],
        "status": peak, "severity_order": list(LEVELS),
        "classification_domain": "FICTIONAL_MISSION_TRAINING_ONLY",
        "basis": basis, "reason": reason, "model_attention_level": model_tier,
        "engineering_attention_level": engineering_tier,
        "models_ready": candidate_ready and both_legacy_ready,
        "measurement_verification_required": bool(quality_issue or apdra_check),
        "explanation": details,
        "actions": [
            "Verify measurement source, cadence, individual context and current readings.",
            "Review model agreement and synthetic engineering deviations independently.",
            "Use authorized mission checklists and notify the responsible crew member if the simulated situation calls for it.",
        ],
        "voice_ready_script": "HealthGuard simulated training. " + GUIDANCE[peak],
        "voice_generation": "DETERMINISTIC_TEMPLATE_NOT_LLM",
        "audible_alert_suggested": peak in ("WARNING","CRITICAL"),
        "voice_requires_user_permission": True,
        "automatic_treatment_or_diagnosis": False,
        "historical_nasa_biomarkers_in_inference": False,
        "live_apdra_applied": apdra is not None and apdra.get("status") != "MODEL_ERROR",
        "clinical_validation": False, "operational_limit_validation": False,
        "disclaimer": ("Training-only combined evidence. Optimal/Check/Warning/Critical are "
                       "fictional monitoring attention labels, not astronaut health, "
                       "NASA operational limit, emergency triage or clinical diagnoses."),
    }


class UnifiedReviewMonitor:
    """Per-crew latest+bounded history; no global status contamination."""
    def __init__(self):
        self._lock = RLock()
        self._latest: dict[str,dict] = {}
        self._history: dict[str,deque] = {}

    def process(self, subject_id: str, sequence: int, packet: dict,
                cnn: dict, comparison: dict, context: dict,
                candidate: dict, engineering: dict, apdra: dict | None = None) -> dict:
        result = compose_review(subject_id, sequence, packet, cnn, comparison,
                                context, candidate, engineering, apdra)
        with self._lock:
            prev = self._latest.get(subject_id)
            if prev and sequence <= prev["sequence"]:
                raise ValueError("Non-increasing PhysioAlert event sequence")
            self._latest[subject_id] = result
            self._history.setdefault(subject_id, deque(maxlen=300)).append(result)
        return result

    def latest(self, subject_id: str) -> dict | None:
        with self._lock:
            return self._latest.get(subject_id)

    def history(self, subject_id: str, limit: int=120) -> list[dict]:
        if not 1 <= limit <= 300:
            raise ValueError("History limit out of range")
        with self._lock:
            return list(self._history.get(subject_id, ()))[-limit:]
