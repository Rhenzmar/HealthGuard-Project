"""Fictional crew and habitat engineering signals, separate from biomedical AI models.

Never treat these fields as NASA observations, live spacecraft telemetry,
clinical biomarkers, or diagnostic outputs. Deterministic so demos/tests are
reproducible. Does not alter the frozen 5-channel CNN input.
"""
from __future__ import annotations
from math import sin, pi
from typing import Any

ENGINEERING_SOURCE = "FICTIONAL_ENGINEERING_SIMULATOR"
CREW_IDS = ("SIM_CREW_01", "SIM_CREW_02", "SIM_CREW_03", "SIM_CREW_04")
SIGNALS: dict[str, dict[str, str]] = {
    "systolic_bp_mmhg": {"label": "Systolic blood pressure", "unit": "mmHg", "system": "cardiovascular", "origin": "SCRIPTED_ESTIMATE_NOT_CUFF"},
    "diastolic_bp_mmhg": {"label": "Diastolic blood pressure", "unit": "mmHg", "system": "cardiovascular", "origin": "SCRIPTED_ESTIMATE_NOT_CUFF"},
    "peripheral_temp_c": {"label": "Peripheral skin temperature", "unit": "°C", "system": "thermal", "origin": "SCRIPTED_ESTIMATE_NOT_SENSOR"},
    "etco2_mmhg": {"label": "End-tidal CO₂", "unit": "mmHg", "system": "pulmonary", "origin": "SCRIPTED_ESTIMATE_NOT_CAPNOGRAPH"},
    "cabin_co2_ppm": {"label": "Cabin carbon dioxide", "unit": "ppm", "system": "environment", "origin": "SCRIPTED_ESTIMATE_NOT_CABIN_SENSOR"},
    "cabin_o2_percent": {"label": "Cabin oxygen fraction", "unit": "%", "system": "environment", "origin": "SCRIPTED_ESTIMATE_NOT_CABIN_SENSOR"},
    "cabin_pressure_kpa": {"label": "Cabin pressure", "unit": "kPa", "system": "environment", "origin": "SCRIPTED_ESTIMATE_NOT_CABIN_SENSOR"},
    "cabin_temp_c": {"label": "Cabin temperature", "unit": "°C", "system": "environment", "origin": "SCRIPTED_ESTIMATE_NOT_CABIN_SENSOR"},
    "cabin_humidity_percent": {"label": "Relative humidity", "unit": "%", "system": "environment", "origin": "SCRIPTED_ESTIMATE_NOT_CABIN_SENSOR"},
    "radiation_rate_usv_h": {"label": "Radiation dose rate", "unit": "µSv/h", "system": "radiation", "origin": "SCRIPTED_ESTIMATE_NOT_DOSIMETER"},
    "cumulative_dose_usv": {"label": "Accumulated simulated dose", "unit": "µSv", "system": "radiation", "origin": "SCRIPTED_ILLUSTRATION_NOT_HISTORICAL_EXPOSURE"},
    "suit_o2_remaining_percent": {"label": "Illustrative suit O₂ reserve", "unit": "%", "system": "suit", "origin": "SCRIPTED_ESTIMATE_NOT_SUIT_SENSOR"},
    "suit_pressure_psi": {"label": "Illustrative suit pressure", "unit": "psi", "system": "suit", "origin": "SCRIPTED_ESTIMATE_NOT_PRESSURE_SENSOR"},
    "suit_battery_percent": {"label": "Illustrative suit battery reserve", "unit": "%", "system": "suit", "origin": "SCRIPTED_ESTIMATE_NOT_BATTERY_SENSOR"}
}

# The trained 17-input CNN uses exactly five physiological and 12 engineering
# signals. Additional HUD-only channels must NEVER silently alter that
# checkpoint's fixed feature order or imply the CNN was retrained.
FROZEN_17CH_ENGINEERING_KEYS = tuple(
    k for k in SIGNALS if k not in {"suit_pressure_psi", "suit_battery_percent"}
)
assert len(FROZEN_17CH_ENGINEERING_KEYS) == 12

def engineering_snapshot(subject_id: str, sequence: int) -> dict[str, Any]:
    if subject_id not in CREW_IDS:
        raise ValueError("Unknown fictional crew subject")
    if not isinstance(sequence, int) or sequence < 0:
        raise ValueError("Sequence must be a non-negative integer")
    crew = CREW_IDS.index(subject_id)
    t = float(sequence)
    # The regular live demonstration is an indefinitely running *rest* stream.
    # Consumables have no resupply/EVA mission clock, so do not drain toward
    # emergencies as an artifact of web-service uptime. Keep the first 10
    # fictional minutes of gradual change, then hold those illustrative values.
    # Scripted suit-power / suit-oxygen failures are injected separately by
    # scenario_engine, not by ordinary live sequence growth.
    nominal_elapsed_seconds = min(t, 600.0)
    p = crew * 1.13
    slow = sin(t/55 + p)
    fast = sin(t/13 + p)
    values = {
        "systolic_bp_mmhg": round(112 + 3*crew + 2*slow, 1),
        "diastolic_bp_mmhg": round(73 + crew + 1.3*fast, 1),
        "peripheral_temp_c": round(33.8 + .14*crew + .25*slow, 2),
        "etco2_mmhg": round(36.5 + .7*crew + 1.2*fast, 1),
        "cabin_co2_ppm": round(640 + 45*slow + 12*fast, 1),
        "cabin_o2_percent": round(20.9 + .03*slow, 2),
        "cabin_pressure_kpa": round(101.2 + .18*slow, 2),
        "cabin_temp_c": round(22.2 + .25*slow, 2),
        "cabin_humidity_percent": round(43 + 2*slow, 1),
        "radiation_rate_usv_h": round(.42 + .04*abs(slow), 3),
        "cumulative_dose_usv": round((.42 + .04*abs(slow)) * nominal_elapsed_seconds/3600, 4),
        "suit_o2_remaining_percent": round(max(0, 94 - .002*nominal_elapsed_seconds - crew*.5), 2),
        # Nominal examples are illustrative, not NASA EMU design specifications.
        "suit_pressure_psi": round(4.3 + .025*sin(t/36 + p), 2),
        # Battery decays gradually across the synthetic EVA sequence.
        "suit_battery_percent": round(max(0, 88 - 1.5*crew - .015*nominal_elapsed_seconds), 2)
    }
    return {
        "subject_id": subject_id,
        "sequence": sequence,
        "source": ENGINEERING_SOURCE,
        "source_kind": "SYNTHETIC_ENGINEERING_TRAINING_VALUES",
        "measurement_origin": "SYNTHETIC_NOT_MEASURED",
        "model_validated": False,
        "clinical_validation": False,
        "values": values,
        "channels": SIGNALS,
        "classification": "NOT_EVALUATED",
        "warning": "Fictional reproducible numbers. No cabin, suit pressure, battery, oxygen, or dosimetry instruments are connected. All displayed numbers are fictional."
    }
