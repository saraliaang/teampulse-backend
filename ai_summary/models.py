from django.db import models


class WeeklyTeamInsight(models.Model):

    team = models.OneToOneField(
        "users.Team",
        on_delete=models.CASCADE,
        related_name="insight",
    )
    # users because Team is in users folder(which is also a package and Django recognize thru the init file )
    avg_mood = models.FloatField()
    avg_workload = models.FloatField()
    completion_rate = models.FloatField()
    pulse_count = models.PositiveIntegerField()
    low_mood_count = models.PositiveIntegerField(default=0)
    low_workload_count = models.PositiveIntegerField(default=0)
    summary = models.TextField()

    year_week = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.team.team_name} - {self.year_week}"
