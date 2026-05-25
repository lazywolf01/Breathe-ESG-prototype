from rest_framework import serializers

from .models import EmissionActivity, Facility, ReviewEvent, SourceBatch, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ("id", "name", "slug")


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ("id", "code", "name", "country")


class SourceBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceBatch
        fields = "__all__"


class ReviewEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewEvent
        fields = ("actor", "action", "note", "before", "after", "created_at")


class EmissionActivitySerializer(serializers.ModelSerializer):
    facility = FacilitySerializer()
    batch = SourceBatchSerializer()
    events = ReviewEventSerializer(many=True, read_only=True)

    class Meta:
        model = EmissionActivity
        fields = "__all__"
