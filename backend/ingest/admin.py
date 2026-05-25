from django.contrib import admin

from .models import EmissionActivity, Facility, ReviewEvent, SourceBatch, Tenant

admin.site.register([Tenant, Facility, SourceBatch, EmissionActivity, ReviewEvent])
