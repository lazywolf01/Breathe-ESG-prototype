from pathlib import Path

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import EmissionActivity, ReviewEvent, SourceBatch, Tenant
from .serializers import EmissionActivitySerializer, SourceBatchSerializer
from .services import import_csv, review_activity, tenant_bootstrap

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "sample_data"


@api_view(["GET"])
def health(_request):
    return Response({"ok": True})


@api_view(["POST"])
def seed(_request):
    EmissionActivity.objects.all().delete()
    SourceBatch.objects.all().delete()
    Tenant.objects.all().delete()
    for source_type, filename in {
        "sap": "sap_material_documents.csv",
        "utility": "utility_meter_export.csv",
        "travel": "concur_travel_expenses.csv",
    }.items():
        import_csv(source_type, (SAMPLE_DIR / filename).read_text(), filename, "Seeded realistic sample")
    return Response(dashboard_payload())


@api_view(["POST"])
def clear_data(_request):
    EmissionActivity.objects.all().delete()
    SourceBatch.objects.all().delete()
    Tenant.objects.all().delete()
    tenant_bootstrap()
    return Response(dashboard_payload())


@api_view(["GET"])
def dashboard(_request):
    return Response(dashboard_payload())


def dashboard_payload():
    tenant_bootstrap()
    qs = EmissionActivity.objects.select_related("facility", "batch", "tenant").prefetch_related("events")
    status_counts = dict(qs.values_list("status").annotate(count=Count("id")))
    source_totals = list(qs.values("batch__source_type").annotate(co2e=Sum("co2e_kg"), rows=Count("id")).order_by("batch__source_type"))
    return {
        "stats": {
            "rows": qs.count(),
            "co2e_kg": qs.aggregate(total=Sum("co2e_kg"))["total"] or 0,
            "status_counts": status_counts,
            "source_totals": source_totals,
        },
        "batches": SourceBatchSerializer(SourceBatch.objects.order_by("-received_at"), many=True).data,
        "activities": EmissionActivitySerializer(qs[:200], many=True).data,
    }


@api_view(["POST"])
def upload(request):
    source_type = request.data.get("source_type")
    file = request.FILES.get("file")
    if source_type not in {"sap", "utility", "travel"} or not file:
        return Response({"error": "source_type and file are required"}, status=400)
    batch = import_csv(source_type, file.read().decode("utf-8-sig"), file.name, file.name)
    return Response(SourceBatchSerializer(batch).data, status=201)


@api_view(["PATCH"])
def review(request, activity_id):
    try:
        activity = EmissionActivity.objects.get(id=activity_id)
        updated = review_activity(
            activity,
            request.data.get("status", "approved"),
            request.data.get("actor", "Analyst"),
            request.data.get("note", ""),
            request.data.get("edits", {}),
        )
        return Response(EmissionActivitySerializer(updated).data)
    except EmissionActivity.DoesNotExist:
        return Response({"error": "Activity not found"}, status=404)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=409)


@api_view(["POST"])
def lock_approved(request):
    actor = request.data.get("actor", "Lead analyst")
    rows = EmissionActivity.objects.filter(status="approved")
    count = 0
    for activity in rows:
        before = {"status": activity.status}
        activity.status = "locked"
        activity.locked_at = timezone.now()
        activity.save(update_fields=["status", "locked_at", "updated_at"])
        ReviewEvent.objects.create(activity=activity, actor=actor, action="locked", before=before, after={"status": "locked"})
        count += 1
    return Response({"locked": count})


def sample_file(_request, filename):
    path = SAMPLE_DIR / filename
    if not path.exists():
        return HttpResponse(status=404)
    return HttpResponse(path.read_text(), content_type="text/csv")
