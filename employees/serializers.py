from rest_framework import serializers
from employees.models import Employee
from users.models import User
from users.serializers import UserSerializer


class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(
        read_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Employee
        fields = "__all__"
