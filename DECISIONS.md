# Decisions

## SAP

I chose a flat-file material document export, not a live OData pull, for the prototype. Real SAP integrations often require customer-specific authorization, middleware, plant/material mappings, and change data capture decisions. A CSV export lets the reviewer see the parser and model clearly while still reflecting SAP realities: material document IDs, plant codes, movement types, German-style dates, and procurement spend.

Handled subset: diesel, petrol, and one spend-based procurement line from material/procurement documents.

Ignored: full IDoc envelopes, BAPI posting semantics, vendor master enrichment, tax handling, purchase-order joins, and SAP authorization.

PM question: Do analysts need to reconcile against finance-approved invoices, or only activity/emissions evidence?

## Utility electricity

I chose portal CSV exports. Facility teams commonly download meter data or bills from utility portals, and CSV is a realistic first integration before utility APIs are approved. The sample includes meter IDs, tariffs, billing periods, account numbers, kWh/MWh units, and a long billing period that should be flagged.

Handled subset: electricity consumption with billing periods and meter/facility mapping.

Ignored: PDF bill extraction, demand charges, time-of-use intervals, taxes, renewable attributes, and calendar-month allocation.

PM question: Should the product calendarize bills into monthly reporting periods, or keep bill periods intact until final reporting?

## Corporate travel

I chose a Concur-style expense export rather than live API ingestion. SAP Concur exposes report and travel APIs, but customer access depends on scopes, datacenter URLs, and product edition. For a four-day prototype, an export preserves the important shape: report IDs, expense categories, airport/station codes, currencies, and rows where distance is missing.

Handled subset: flights, hotels, rail, and taxi lines.

Ignored: OAuth, user identity sync, itinerary APIs, cabin class, radiative forcing uplift, hotel country-specific factors, and receipt images.

PM question: Should flight emissions be estimated from booked itinerary distance, reimbursed expense lines, or both with duplicate detection?

## Review workflow

I used simple statuses: pending, flagged, approved, rejected, locked. Suspicious rows are not blocked; they are highlighted so an analyst can still approve with context.

PM question: Who is allowed to lock rows, and does locking happen per facility, period, batch, or reporting year?
