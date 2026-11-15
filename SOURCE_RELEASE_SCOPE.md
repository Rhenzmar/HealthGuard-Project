# Source-release scope and verification

This repository is a limited public release for NASA Space Apps Challenge 2026. It presents selected implementation files from the private development repository without exposing its commit history, model weights, datasets, deployment credentials, or third-party anatomical/portrait assets.

**What is available:** original simulated engineering signal generation, telemetry input handling, contextual PhysioAlert evaluation, experimental simulated-live baseline stability, scripted frontend scenarios, health routine and user interface utilities. See `source/`.

**What is not available:** complete production frontend/API, full integration scripts, NASA historical assay datasets, trained checkpoint weights, third-party anatomy assets, dependency locks, private development history, or a reproducible standalone deployment.

**Scientific status:** five-channel synthetic-model benchmark and internal synthetic integration testing are not clinical tests. Nine scenario types are available in the demonstration; the documented formal integration audit used seven scenarios across four fictional crew (28 combinations, 168 checkpoints). The exploratory expanded CNN has 17 selected synthetic inputs, and has not been externally validated on actual continuous astronaut multichannel measurements.

**Rights:** The MIT LICENSE applies to original source and documentation released here, to the extent owned by the contributors. It does not override third-party rights. The original application uses third-party open-source dependencies and assets with their own terms. The project team must verify permission from all code contributors before broader redistribution.
