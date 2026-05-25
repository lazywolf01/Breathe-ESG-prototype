from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Facility(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="facilities")
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=160)
    country = models.CharField(max_length=2, default="IN")

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class SourceBatch(models.Model):
    SOURCE_CHOICES = [
        ("sap", "SAP fuel/procurement"),
        ("utility", "Utility electricity"),
        ("travel", "Corporate travel"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_name = models.CharField(max_length=160)
    ingestion_mode = models.CharField(max_length=80)
    source_reference = models.CharField(max_length=160)
    received_at = models.DateTimeField(default=timezone.now)
    row_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.source_type}:{self.source_reference}"


class EmissionActivity(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending review"),
        ("flagged", "Flagged"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("locked", "Locked for audit"),
    ]
    SCOPE_CHOICES = [("scope_1", "Scope 1"), ("scope_2", "Scope 2"), ("scope_3", "Scope 3")]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(SourceBatch, on_delete=models.CASCADE, related_name="activities")
    external_id = models.CharField(max_length=120)
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=80)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    description = models.CharField(max_length=240)
    raw_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    raw_unit = models.CharField(max_length=24)
    normalized_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    normalized_unit = models.CharField(max_length=24)
    emission_factor = models.DecimalField(max_digits=10, decimal_places=5)
    co2e_kg = models.DecimalField(max_digits=14, decimal_places=3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    suspicion_reason = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict)
    edited_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.CharField(max_length=120, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("tenant", "batch", "external_id")
        ordering = ("-activity_date", "external_id")

    def __str__(self):
        return f"{self.external_id} {self.category} {self.co2e_kg} kg"


class ReviewEvent(models.Model):
    activity = models.ForeignKey(EmissionActivity, on_delete=models.CASCADE, related_name="events")
    actor = models.CharField(max_length=120)
    action = models.CharField(max_length=40)
    note = models.TextField(blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
