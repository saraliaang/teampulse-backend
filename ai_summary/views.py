from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from pulse_logs.utils import get_time_index
from users.models import Team
from users.permissions import IsStaff, IsSuperUser

from .models import WeeklyTeamInsight
from .serializers import InsightSerializer
from .services.llm_generator import (
    LLMGenerationError,
    generate_team_summary,
)
from .services.metrics import calculate_team_metrics


class InsightDetail(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsSuperUser | IsStaff,
    ]

    def get_team(self, request, team_id):
        team = get_object_or_404(Team, pk=team_id)

        if (
            not request.user.is_superuser
            and team.team_manager != request.user.id
        ):
            raise PermissionDenied("You do not manage this team.")

        return team

    def get(self, request, team_id):
        team = self.get_team(request, team_id)
        insight = get_object_or_404(
            WeeklyTeamInsight,
            team=team,
        )

        return Response(InsightSerializer(insight).data)

    def post(self, request, team_id):
        team = self.get_team(request, team_id)
        requested_year_week = request.data.get("year_week")

        if requested_year_week is None:
            requested_year_week = get_time_index(
                timezone.now()
            )["year_week"]

        try:
            year_week = int(requested_year_week)
        except (TypeError, ValueError):
            return Response(
                {"detail": "year_week must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        metrics = calculate_team_metrics(team, year_week)

        if metrics["completion_rate"] < 50:
            return Response(
                {
                    "detail": "Not enough responses to generate an insight.",
                    "metrics": metrics,
                },
                status=status.HTTP_200_OK,
            )

        existing = WeeklyTeamInsight.objects.filter(
            team=team
        ).first()

        if (
            existing
            and existing.year_week == year_week
            and existing.pulse_count == metrics["pulse_count"]
        ):
            return Response(
                {
                    "created": False,
                    "regenerated": False,
                    "insight": InsightSerializer(existing).data,
                },
                status=status.HTTP_200_OK,
            )

        try:
            generated_summary = generate_team_summary(metrics)
        except LLMGenerationError:
            return Response(
                {
                    "detail": (
                        "The team insight could not be generated "
                        "right now."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        insight, created = WeeklyTeamInsight.objects.update_or_create(
            team=team,
            defaults={
                "year_week": year_week,
                "avg_mood": metrics["avg_mood"],
                "avg_workload": metrics["avg_workload"],
                "completion_rate": metrics["completion_rate"],
                "pulse_count": metrics["pulse_count"],
                "low_mood_count": metrics["low_mood_count"],
                "low_workload_count": metrics[
                    "low_workload_count"
                ],
                "summary": generated_summary,
            },
        )

        return Response(
            {
                "created": created,
                "regenerated": not created,
                "insight": InsightSerializer(insight).data,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )
