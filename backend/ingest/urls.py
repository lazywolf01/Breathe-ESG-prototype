from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health),
    path("seed/", views.seed),
    path("dashboard/", views.dashboard),
    path("upload/", views.upload),
    path("activities/<int:activity_id>/review/", views.review),
    path("lock-approved/", views.lock_approved),
    path("samples/<str:filename>", views.sample_file),
]
