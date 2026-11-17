# Stuffing Suite — consolidated shipment planning

One Streamlit interface for the five historical container-stuffing variants: 20 ft, 40 ft, 40 HC, DCD and DND. This is **weight/volume shipment allocation**, not dimensional 3D packing or a guaranteed physical fit. Cargo Fit Planner is a separate project and is not modified here.

## Run locally

Python 3.12:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/streamlit run app.py
.venv/bin/python -m unittest discover -s tests -v
```

The lock captures the tested environment. `requirements.txt` describes permitted direct dependency ranges.

## What changed

- One equipment selector replaces five application entrypoints.
- Payload and volume are editable, with provenance shown next to each preset.
- Dry-container reference maxima come from [Maersk](https://www.maersk.com/support/faqs/cargo-weight-limit), checked 2026-11-17: 20 dry 33.2 m³/28,300 kg; 40 dry 67.7 m³/28,870 kg; 40 HC 76.4 m³/28,690 kg. Allocated equipment and legal route limits vary. Working values must be reduced for actual operations where necessary.
- DCD/DND remain custom legacy labels, not externally verified equipment types. Their 58 m³/24,000 kg starting values are explicitly unverified.
- Rates are editable per-equipment scenario tables with route, date, currency, basis, scope, source and included charges. Missing, expired, wrong-route or overlapping rates produce an unpriced/ambiguous result, never free transport. Rate availability never disqualifies a physically allocatable job.
- CSV/XLSX column mapping accepts legacy WEIGHT/CBM/Job No headers. All weights are explicitly kg. Jobs and their positive priority values can be edited before planning.
- Every job is either assigned exactly once or returned with an unassigned reason; oversize jobs are no longer silently lost.
- JSON export includes the actual jobs, assumptions, rate records and equipment provenance. No uploaded jobs are persisted to disk, shared cache or database. Downloaded reports can contain business data; handle them accordingly.

## Pricing is not a fabricated market average

The old 78,000–145,000 constants have unknown currency/lane/date/service provenance. They are preserved verbatim in backups, not promoted to current defaults. [Maersk rate lookup](https://www.maersk.com/support/faqs/how-to-lookup-rates) needs route/date; [quote inputs](https://www.maersk.com/support/faqs/how-to-get-a-rate-quote) include commodity, equipment, weight and readiness. A defensible populated price preset requires a current carrier tariff or quote for the intended lane. No universal average is represented here.

## Optimization and migration limitations

SCIP chooses one load at a time to maximize priority-weighted normalized weight plus volume utilization. Repetition is a heuristic for the complete plan, not global minimum vehicles or cost. Pricing is an estimate applied after allocation, not a carrier booking. Solver limits: 1 second per load, 15 seconds overall; unresolved jobs are reported. Limit: 500 jobs, 5 MB upload, 20 MB expanded XLSX archive.

The old fixed port-days lookup is preserved in backups but deliberately not used as a current transit-time promise. Priority is explicit instead of inferred from a port code and stale ETD assumptions. Old unreachable add/remove-console UI is not reproduced; edit job data and rerun. Legacy scripts are evidence only and must not be imported or executed in the new runtime.

No authentication, database, multi-user organization workspace, live carrier API, hazardous-goods handling, axle model or 3D fit validation is provided. Session-local state is not a substitute for access controls. Do not expose company records on a public demo; use only synthetic data until access/privacy requirements are agreed.

## Backups and provenance

`backups/<original-repository>/<HEAD-commit>/` contains byte-exact source snapshots, verified against original Git blob SHA-1 identifiers. Adjacent JSON manifests include repository visibility, tree, original blob IDs and commit history metadata. The connector strips some final newlines; only a newline representation matching the original Git blob hash was restored. These snapshots are not full bare Git mirrors. Full source history remains preserved, untouched, in each original GitHub repository. No original repo, branch, deployed app or commit was deleted or changed.

Three source repos were private at collection. The repository owner explicitly authorized public publication of this consolidation and its source backups on 2026-11-17. Original commit authors and messages remain in manifests; no license/ownership change is granted. Review found no credentials, customer records or company identifiers in the archived source; this is not a security certification. Existing originals remain the rollback point. See `docs/provenance.json` for exact versions.

## Hosting preparation, not deployed

A Dockerfile allowlists only the new app, engine, equipment config and locked dependencies, excluding archives and business files. It binds to `$PORT`, retains Streamlit's CORS/XSRF defaults, disables usage telemetry and runs as a non-root user. On Render this would be a Docker web service with `/_stcore/health` health check. Do not create paid resources without approved budget. Render connection currently needs reconnection before account-level work; no service was created, modified or deployed by this consolidation.

Before production: authentication if real records are used, source quote/default lane, actual browser/upload/export verification, container build and deployment health verification. Do not change existing app URLs until the replacement is tested and accepted.

Current scenario behavior: switching equipment starts a fresh scenario and may reset earlier working values/rate edits. The UI warns before switching; download the plan first. Persistent scenario storage/import is not implemented.
