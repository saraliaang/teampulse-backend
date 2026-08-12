from rest_framework import serializers
from .models import WeeklyTeamInsight


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyTeamInsight
        fields = "__all__"


# read_only means preventing update from the frontend, but only allows updating thru backend using serializer.save()
