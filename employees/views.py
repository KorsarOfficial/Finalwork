from rest_framework import viewsets, permissions
from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления сотрудниками.
    Предоставляет CRUD операции для модели Employee.
    """

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_permissions(self):
        """
        Определяет права доступа для разных действий (actions) в ViewSet.
        Права доступа зависят от того, какой пользователь выполняет действие.
        """
        if self.action == "list" or self.action == "retrieve":
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        При создании сотрудника привязываем текущего пользователя (администратора) к сотруднику.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        При обновлении сотрудника также привязываем текущего пользователя (администратора).
        """
        serializer.save(user=self.request.user)
