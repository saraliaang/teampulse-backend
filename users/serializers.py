from django.apps import apps
from rest_framework import serializers

from .models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Call the base class __init__ method to set up all fields
        super().__init__(*args, **kwargs)

        # Logic to check if we are in a 'create' (POST) scenario
        # self.instance is None when a new object is being created
        if self.instance is None:
            # Explicitly set these fields as required only for creation
            self.fields["first_name"].required = True
            self.fields["last_name"].required = True
        # For updates (self.instance is not None), the fields default to
        # the requirements defined by the model (or the Meta extra_kwargs below),
        # making them optional for PUT/PATCH.

    class Meta:
        model = CustomUser
        fields = "__all__"
        extra_kwargs = {  # noqa: RUF012
            "password": {
                "write_only": True,
                "required": True,
                "allow_blank": False,
            },
            "first_name": {"allow_blank": False},
            "last_name": {"allow_blank": False},
        }

    def create(
        self, validated_data
    ):  # validated - once serializers validate data, it will pass them into function so that it is ensured the data are valid

        validated_data["is_staff"] = False
        validated_data["is_superuser"] = False

        return CustomUser.objects.create_user(**validated_data)


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("users.Team")
        fields = "__all__"


class KudosSerializer(serializers.ModelSerializer):
    sender_first_name = serializers.CharField(
        source="sender.first_name", read_only=True
    )  # Derive from sender FK
    sender_last_name = serializers.CharField(
        source="sender.last_name", read_only=True
    )  # Derive from sender FK

    class Meta:
        model = apps.get_model("users.Kudos")
        fields = "__all__"
        extra_kwargs = {  # noqa: RUF012
            "sender": {"read_only": True}
        }  # Prevent client from setting sender

    def create(self, validated_data):
        # Set sender from the authenticated user in context
        user = self.context["request"].user
        validated_data["sender"] = user

        # Populate denormalized fields
        validated_data["sender_first_name"] = user.first_name
        validated_data["sender_last_name"] = user.last_name

        return super().create(validated_data)
