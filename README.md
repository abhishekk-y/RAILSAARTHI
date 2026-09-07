# RailSaarthi

**Railway Intelligent Asset & Infrastructure Scheduling, Availability and Resilient Timetable Harmonization System**

RailSaarthi is a local-first decision intelligence prototype for coordinating Engineering, S&T and TRD maintenance possessions against passenger and freight movements. It uses deterministic synthetic data, a priority engine, a greedy benchmark, and Google OR-Tools CP-SAT scheduling. Synthetic results are labeled and are not Indian Railways operational data.

## Run locally

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000`. On Windows, `./start.ps1` installs dependencies and starts the service. The OpenAPI contract is at `/docs`.

## Working vertical slice

1. Load SIH DEMO SCENARIO with reproducible seed 42.
2. Inspect the generated corridor, train movements and maintenance backlog.
3. Review the priority-greedy baseline.
4. Run CP-SAT optimization with hard section, train, crew, deadline and approved-block constraints.
5. Compare calculated KPIs and inspect a task's priority and slot explanation.
6. Advance the digital-twin clock or trigger a 45-minute freight disruption from the live control strip.
7. Inspect joint-block opportunities, conflict diagnostics, data quality, Monte Carlo robustness and CSV export through the API.

## Public real-data mode

The **Load real OSM map** control fetches current public railway geometry from the OpenStreetMap Overpass API and renders it with Leaflet. The map displays source attribution and fetch time. This is real infrastructure geometry, not a claim that OpenStreetMap contains railway possession authority or live Indian Railways control data.

Optional GTFS-Realtime ingestion is enabled with `RAILSAARTHI_GTFS_RT_URL`. Install the decoder from `requirements.txt`, then use `/api/live/refresh?gtfs_url=...`. The feed must be a public, authorized GTFS-Realtime endpoint. GTFS updates are displayed as external observations and are not silently converted into safe block permissions. The optimizer continues to use the canonical validated timetable model until an operator-approved adapter maps the feed into it.

Public web data is an optional integration path. The deterministic synthetic scenario remains the offline fallback and is always labeled as demonstration data.

## Realtime and analytics routes

The local service exposes `/ws/events` for optimization, simulation and replan events, `/api/replan` for disruption recovery, `/api/simulation/state` and `/api/simulation/tick` for the digital twin, `/api/search?query=F-001&kind=trains` for train-number lookup, `/api/joint-blocks`, `/api/conflicts`, `/api/data-quality`, `/api/robustness`, `/api/integration/status`, and `/api/export/blocks.csv`.

## Request Workflow and Roles

The backlog is now a request workflow rather than a read-only list. `/api/requests` supports department, status and priority filters. `/api/requests/{request_id}` supports status transitions, while `/api/roles/permissions` exposes the permission matrix. Only `Control Office` and `Administrator` roles can approve or reject a request; planners and departments can inspect and submit work without bypassing operational approval.

## Local AI models

`/api/models/train` trains deterministic duration, failure-risk, priority, and freight-forecast models from seeded synthetic history. `/api/models` exposes registry metadata and validation metrics. `/api/models/predict/{task_id}` returns priority, risk, and duration interval estimates; `/api/models/freight-forecast` returns hourly demand estimates. These models provide prioritization and planning estimates only; CP-SAT hard safety constraints remain authoritative, and synthetic metrics are not production claims.

Authorized Indian Railway data can replace the synthetic training source with `POST /api/railway-data/import`. The payload requires `source_name`, `source_url`, `authority`, and at least 10 validated maintenance records containing criticality, safety risk, defect severity, crew size, duration, failure label, and isolation flags. After import, `/api/railway-data/statistics` reports source-backed aggregates and all four models are retrained with `1.0-imported` provenance. No Indian Railway operational dataset is bundled or invented in this repository.

## Data transparency

The demo corridor is fictional: Sampur Jn, Kalyanpur, Nandipur, Vikas Nagar and Shivapur Jn. Generated records contain `synthetic=true`, seed and generator version. Production adapters can later implement TMS, SMMS, TDMS, COA, timetable and goods forecast contracts without changing the optimizer model.

## Scope and limitations

The current runnable slice uses in-memory persistence and a 24-hour planning horizon. PostgreSQL, migrations, production authentication, live adapters, and 3D visualization remain deployment extensions. The request approval workflow, CP-SAT scheduling, digital-twin simulation and analytics are implemented locally. No safety authority is delegated to the software.
