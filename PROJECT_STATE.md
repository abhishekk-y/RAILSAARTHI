# Project State

## Completed

- Phase 0 architecture freeze documented in `ARCHITECTURE.md`.
- Phase 1 deterministic synthetic corridor generator with seed and metadata.
- Canonical models for stations, assets, trains, tasks, blocks, scenarios and schedules.
- Rule-based priority score with safety override behavior.
- Priority greedy baseline.
- OR-Tools CP-SAT scheduler with optional intervals, section and crew exclusivity, train separation, deadlines and fixed blocks.
- KPI comparison endpoint and task-level explanation endpoint.
- Local control-office UI with timeline, schematic corridor, critical tasks, solver status and baseline comparison.
- Windows and Linux start/stop scripts.
- Docker image and compose entrypoint.
- Joint-block opportunity detection with explicit compatibility rules.
- Digital-twin event stream, simulation clock and deterministic state snapshots.
- Freight-delay dynamic replanning endpoint with old/new plan comparison.
- WebSocket event hub for optimization, replan and simulation events.
- Visible live twin controls in the command center.
- Monte Carlo robustness report with seeded duration uncertainty.
- Conflict diagnostics, data-quality score, synthetic adapter status and CSV export.
- OpenStreetMap Overpass public railway-geometry adapter with Leaflet rendering and attribution.
- Optional GTFS-Realtime decoder boundary with explicit operator-validation guardrail.
- Universal operations search for train numbers, maintenance tasks, assets, departments and corridors.
- Sidebar operation modules activate their corresponding search scope instead of being inert controls.
- Offline trained duration, failure-risk, priority, and freight-forecast models with registry metadata, synthetic validation metrics and uncertainty intervals.
- Validated Indian railway data import contract with source authority, URL, provenance, statistics, and immediate four-model retraining.

## API routes

`/api/health`, `/api/scenario`, `/api/scenario/load`, `/api/tasks`, `/api/trains`, `/api/search`, `/api/blocks`, `/api/optimization/run`, `/api/metrics/availability`, `/api/tasks/{task_id}/explanation`, `/api/models`, `/api/models/train`, `/api/models/predict/{task_id}`, `/api/models/freight-forecast`, `/api/railway-data/import`, `/api/railway-data/status`, `/api/railway-data/statistics`, `/api/joint-blocks`, `/api/replan`, `/api/simulation/state`, `/api/simulation/tick`, `/api/simulation/events`, `/api/live/map`, `/api/live/refresh`, `/api/conflicts`, `/api/data-quality`, `/api/robustness`, `/ws/events`.

## Validation status

Validated with Python 3.13.1 and OR-Tools 9.12: `4 passed`; seeded CP-SAT returns `OPTIMAL`; imported-record workflow returns `IMPORTED_REAL_DATA` and `1.0-imported` model versions; all four trained models appear in the registry; task predictions expose priority, risk and duration intervals; freight forecasts return hourly estimates; live status, quality and health routes return HTTP 200; browser CP-SAT run displays `OPTIMAL` and a measured runtime; public OpenStreetMap fetch rendered 1,945 railway features in Leaflet. No real Indian Railway dataset is bundled. Node syntax validation passes for `frontend/app.js`. Docker image validation is pending because Docker Desktop is not running on the host. The in-process WebSocket harness did not complete a receive assertion and needs runtime-browser validation.

## Known boundaries

Persistence, auth, production railway timetable adapters, multi-day rolling horizon, PDF/Excel export, advanced ML and 3D twin remain planned modules. Public OSM geometry is working; live GTFS-Realtime ingestion is contract-ready and only becomes optimizer input after validation. The WebSocket event hub and deterministic twin are implemented, but production broker durability and multi-instance delivery are not yet represented.

## Next actions

Install Python 3.12+, run the backend smoke test, execute the golden scenarios, then add database persistence and joint-block aggregation as the next implementation stage.
