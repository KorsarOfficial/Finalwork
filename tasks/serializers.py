from rest_framework import serializers
from .models import Task
from employees.models import Employee


class TaskSerializer(serializers.ModelSerializer):
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        required=False,
        allow_null=True,
        label="Assignee",
    )
    creator = serializers.PrimaryKeyRelatedField(read_only=True, label="Creator")
    updater = serializers.PrimaryKeyRelatedField(
        read_only=True, required=False, allow_null=True, label="Updater"
    )

    class Meta:
        model = Task
        fields = "__all__"
