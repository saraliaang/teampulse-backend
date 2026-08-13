from django.urls import path

from .views import InsightDetail


urlpatterns = [
    path(
        "team-insights/<int:team_id>/",
        InsightDetail.as_view(),
        name="team-insight-detail",
    ),
]
