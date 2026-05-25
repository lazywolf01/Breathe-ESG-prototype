import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO

from django.utils import timezone

from .models import EmissionActivity, Facility, ReviewEvent, SourceBatch, Tenant


UNIT_FACTORS = {
    "L": ("liter", Decimal("1")),
    "liter": ("liter", Decimal("1")),
    "kWh": ("kWh", Decimal("1")),
    "MWh": ("kWh", Decimal("1000")),
    "km": ("km", Decimal("1")),
    "mile": ("km", Decimal("1.60934")),
    "night": ("night", Decimal("1")),
    "INR": ("INR", Decimal("1")),
}

EMISSION_FACTORS = {
    "diesel": Decimal("2.68000"),
    "petrol": Decimal("2.31000"),
    "electricity_india_grid": Decimal("0.71600"),
    "flight_short_haul": Decimal("0.15800"),
    "flight_long_haul": Decimal("0.11000"),
    "hotel_night": Decimal("18.00000"),
    "rail": Decimal("0.04100"),
    "taxi": Decimal("0.18000"),
    "procurement_spend": Decimal("0.00032"),
}


def parse_date(value):
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date: {value}")


def normalize(quantity, unit):
    normalized_unit, multiplier = UNIT_FACTORS.get(unit, (unit, Decimal("1")))
    return Decimal(str(quantity)) * multiplier, normalized_unit


def tenant_bootstrap():
    tenant, _ = Tenant.objects.get_or_create(slug="acme-manufacturing", defaults={"name": "ACME Manufacturing"})
    facilities = {
        "PL01": "Pune Plant",
        "PL02": "Chennai Assembly",
        "HQ01": "Bengaluru HQ",
    }
    for code, name in facilities.items():
        Facility.objects.get_or_create(tenant=tenant, code=code, defaults={"name": name, "country": "IN"})
    return tenant


def suspicion_for(row, normalized_quantity, normalized_unit, source_type):
    reasons = []
    if row.get("facility_code") in ("", None):
        reasons.append("Missing facility mapping")
    if normalized_quantity <= 0:
        reasons.append("Non-positive quantity")
    if source_type == "utility" and row.get("period_start") and row.get("period_end"):
        start, end = parse_date(row["period_start"]), parse_date(row["period_end"])
        if (end - start).days > 45:
            reasons.append("Billing period longer than 45 days")
    if source_type == "sap" and normalized_unit == "liter" and normalized_quantity > 5000:
        reasons.append("Fuel volume is unusually high for one posting")
    if source_type == "travel" and row.get("category") == "flight" and normalized_quantity == 0:
        reasons.append("Flight row has no distance; airport lookup needed")
    return "; ".join(reasons)


def import_csv(source_type, csv_text, source_reference="sample", source_name="Sample import"):
    tenant = tenant_bootstrap()
    batch = SourceBatch.objects.create(
        tenant=tenant,
        source_type=source_type,
        source_name=source_name,
        source_reference=source_reference,
        ingestion_mode={"sap": "flat-file export", "utility": "portal CSV", "travel": "Concur-style expense export"}[source_type],
    )
    rows = list(csv.DictReader(StringIO(csv_text)))
    failed = 0
    for row in rows:
        try:
            facility = Facility.objects.filter(tenant=tenant, code=row.get("facility_code", "")).first()
            qty, unit = normalize(row["quantity"], row["unit"])
            factor_key = row["factor_key"]
            factor = EMISSION_FACTORS[factor_key]
            co2e = qty * factor
            reason = suspicion_for(row, qty, unit, source_type)
            status = "flagged" if reason else "pending"
            activity = EmissionActivity.objects.create(
                tenant=tenant,
                facility=facility,
                batch=batch,
                external_id=row["external_id"],
                activity_date=parse_date(row["activity_date"]),
                period_start=parse_date(row["period_start"]) if row.get("period_start") else None,
                period_end=parse_date(row["period_end"]) if row.get("period_end") else None,
                category=row["category"],
                scope=row["scope"],
                description=row["description"],
                raw_quantity=Decimal(str(row["quantity"])),
                raw_unit=row["unit"],
                normalized_quantity=qty,
                normalized_unit=unit,
                emission_factor=factor,
                co2e_kg=co2e,
                status=status,
                suspicion_reason=reason,
                raw_payload=row,
            )
            ReviewEvent.objects.create(activity=activity, actor="system", action="ingested", after={"status": status})
        except Exception:
            failed += 1
    batch.row_count = len(rows)
    batch.failed_count = failed
    batch.save(update_fields=["row_count", "failed_count"])
    return batch


def review_activity(activity, action, actor, note="", edits=None):
    if activity.status == "locked":
        raise ValueError("Locked rows cannot be edited")
    before = {"status": activity.status, "edited_payload": activity.edited_payload}
    if edits:
        activity.edited_payload = {**activity.edited_payload, **edits}
    activity.status = action
    activity.reviewed_by = actor
    activity.reviewed_at = timezone.now()
    activity.save()
    ReviewEvent.objects.create(
        activity=activity,
        actor=actor,
        action=action,
        note=note,
        before=before,
        after={"status": activity.status, "edited_payload": activity.edited_payload},
    )
    return activity
