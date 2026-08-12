from django.contrib.auth import get_user_model
from pulse_logs.models import PulseLog
from django.db.models import Avg


def calculate_team_metrics(team, year_week):
    CustomUser = get_user_model()
    members = CustomUser.objects.filter(
        team=team,
        is_staff=False,
        is_active=True,
    )

    logs = PulseLog.objects.filter(
        team=team.id,
        year_week=year_week,
    )

    member_count = members.count()
    checked_in_count = logs.count()

    averages = logs.aggregate(
        avg_mood=Avg("mood__value"),
        avg_workload=Avg("workload__value"),
    )
    # the aggregate return dictionary pair
    # e.g.{ avg_mood: 3.2, avg_workload: 3.1 }

    low_mood_count = logs.filter(mood__value__lte=2).count()

    low_workload_count = logs.filter(workload__value__lte=2).count()

    avg_mood = averages["avg_mood"]
    avg_workload = averages["avg_workload"]

    completion_rate = (
        round(checked_in_count / member_count * 100, 1) if member_count else 0.0
    )

    return {
        "pulse_count": checked_in_count,
        "completion_rate": completion_rate,
        "avg_mood": (round(avg_mood, 2) if avg_mood is not None else None),
        "avg_workload": (round(avg_workload, 2) if avg_workload is not None else None),
        "low_mood_count": low_mood_count,
        "low_workload_count": low_workload_count,
    }
