# HealthGuard

**AI-assisted astronaut health monitoring, physiological anomaly screening and mission-support research prototype**  
NASA Space Apps Challenge 2026 · **CNHS-STE**

[**Open the live demonstration**](https://healthguard-dashboard.onrender.com/) · [NASA Space Apps project page](https://www.spaceappschallenge.org/2026/find-a-team/cnhs-ste/?tab=project)

> This is an interactive, **nonclinical research prototype**, not flight-ready or certified astronaut healthcare. All continuous crew and suit readings in the app are **simulated**, not measurements from real astronauts or connected wearable/suit sensors.

## The idea

HealthGuard explores how personalized reference checks, experimental anomaly-screening models, reliable data handling, and understandable alerts could help astronauts and ground teams notice unusual patterns during long missions. Its frontend demonstrates a fictional crew monitoring experience: independent simulated streams, trends, interactive anatomy, educational health routines, a mission HUD and user-controlled training scenarios.

## See it in action

- **Mission Dashboard and Crew Telemetry:** switch between four fictional astronauts, inspect physiological trends and view PhysioAlert evidence summaries.
- **Body Explorer:** explore three monitored systems: cardiovascular, breathing/oxygen and thermal regulation.
- **Health Routine and Health Library:** activities, educational explanations and source-labeled historical NASA research.
- **Mission Control and Mission HUD:** fictional spacecraft and suit instrumentation displays.
- **Scenario Lab:** nine scripted abnormal events (e.g. oxygenation, thermal, cabin/suit issues), with clear simulated status and optional critical narration.
- **Guided Tour:** eight narrated steps with the explanations distinct from short screen text.

## Where do the data come from?

**Simulated demo:** five original physiological channels, four additional separately scripted physiological estimates and engineering telemetry are generated on the backend for four fictional crew. An experimental 17-input CNN uses five physiological inputs plus twelve selected synthetic engineering/estimate inputs. The 17-input CNN is synthetic-trained, not clinically validated on real NASA 17-input records.

**Historical NASA research:** independent, actual NASA OSD-569 and OSD-575 pre/postflight laboratory biomarker records and a separate ISS RR-1 environmental dataset were evaluated retrospectively. These are not live readings from the fictional crew or inputs to the deployed 17-input model.

## Algorithms and results

HealthGuard combines a frozen five-channel 1D-CNN autoencoder, a shrinkage-covariance numerical novelty comparator, an experimental 17-input candidate, contextual checks, an experimental personal-baseline APDRA review and deterministic PhysioAlert attention labels. **OPTIMAL / CHECK / WARNING / CRITICAL** are demonstration attention tiers, not medical or NASA operational severity levels.

In a **seven-event** synthetic integration audit, four crew profiles were tested across 28 event/person combinations and 168 backend/model evaluations. A subsequent UI release offers nine event types. These tests demonstrate software integration on injected synthetic disturbances, **not real-world diagnostic sensitivity**.

In retrospective NASA laboratory analysis (OSD-569 and OSD-575), 8,783 numeric values were processed. For median-only screens, 272 of 829 flags (32.8%) were not stable under individual reference omission. This is not a measured false-positive rate or an astronaut medical-outcome improvement.

## Supporting resources

- [System architecture](ARCHITECTURE.md)
- [Results and limitations](RESULTS_AND_LIMITATIONS.md)
- [Research sources and provenance](SOURCES.md)

The app is a research and education demonstration. No physical sensors, spacecraft infrastructure, or dynamic medical LLM are connected. Voice guidance is scripted browser text-to-speech. ChatGPT (OpenAI) assisted with research planning, coding, testing, UI and documentation; all claims remain the team's responsibility.

**NASA does not endorse, certify or medically validate HealthGuard.**

This public reader repository is informational and intentionally excludes private source history, credentials, model checkpoints and data files. It does not grant rights to third-party content.
