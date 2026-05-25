# Data Model

The core model is `EmissionActivity`: one normalized activity row that can be reviewed, edited, approved, rejected, and locked for audit. It keeps the source row intact in `raw_payload`, stores any analyst changes separately in `edited_payload`, and links to `ReviewEvent` records for the audit trail.

## Main entities

- `Tenant`: isolates client data. The prototype seeds one tenant, but every facility, batch, and activity is tenant-scoped.
- `Facility`: maps plant/site codes such as SAP `WERKS` or a utility meter assignment to a human-readable site.
- `SourceBatch`: records a single ingestion event, including source type, source reference, ingestion mode, received time, row count, and failures.
- `EmissionActivity`: normalized row with category, Scope 1/2/3, raw and normalized units, emission factor, CO2e, status, suspicion reason, and source lineage.
- `ReviewEvent`: append-only audit log for ingestion, approval, rejection, edits, and audit locking.

## Why this shape

The assignment is mostly about messy source truth. I kept source-specific facts in `raw_payload` and normalized only the fields the analyst needs across all sources: tenant, facility, date/period, category, scope, quantity, unit, factor, CO2e, status, and review metadata.

This avoids three brittle per-source schemas while still preserving evidence. If an auditor asks where a number came from, the app can point to `SourceBatch.source_reference`, `raw_payload`, `created_at`, and the review events that happened after import.

## Multi-tenancy

Tenant is an explicit foreign key on batches, facilities, and activities. In production I would enforce tenant filtering in authentication middleware or query managers. The prototype has no login system, so the model shows the boundary without pretending it has complete access control.

## Source of truth

The source system remains the truth for raw facts. The normalized row is the truth for review state. The app never overwrites `raw_payload`; analyst changes go into `edited_payload`, and review actions append `ReviewEvent` rows.

## Unit normalization

The import service normalizes:

- litres to litres for liquid fuel
- MWh to kWh for electricity
- miles to kilometres for travel
- nights as hotel-night activity units
- spend as INR for spend-based procurement

The emission factor is stored on the row at import time. That is deliberate: future factor-library changes should not silently rewrite an already reviewed audit row.

## Audit locking

Approved rows can be locked. Locked rows cannot be edited by the review endpoint. This is the minimum useful control for a pre-audit sign-off workflow.
