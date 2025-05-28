import logging
from rest_framework import viewsets, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Task, Employee
from .serializers import TaskSerializer
from employees.serializers import EmployeeSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .permissions import IsTaskAssigneeOrAdmin
from django.db.models import Count, Q

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления задачами.
    Предоставляет CRUD операции для модели Task, а также фильтрацию, поиск и сортировку.
    """

    queryset = Task.objects.all()  # Получаем все задачи из базы данных
    serializer_class = (
        TaskSerializer  # Указываем сериализатор для преобразования данных
    )
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]  # Подключаем фильтры
    filterset_fields = ["status", "assignee"]  # Указываем поля для фильтрации
    search_fields = ["name", "description"]  # Указываем поля для поиска
    ordering_fields = ["deadline", "priority"]  # Указываем поля для сортировки

    def get_permissions(self):
        """
        Определяет права доступа для разных действий (actions) в ViewSet.
        Права доступа зависят от того, какой пользователь выполняет действие и к какой задаче он пытается получить доступ.
        """
        if self.action == "retrieve":  # Если действие - получение конкретной задачи
            permission_classes = [
                IsTaskAssigneeOrAdmin
            ]  # Разрешаем доступ назначенному пользователю или администратору
        elif self.action == "create":  # Если действие - создание задачи
            permission_classes = [
                permissions.IsAdminUser
            ]  # Разрешаем только администратору
        elif self.action == "update":  # Если действие - обновление задачи
            permission_classes = [
                permissions.IsAdminUser
            ]  # Разрешаем только администратору
        elif self.action == "destroy":  # Если действие - удаление задачи
            permission_classes = [
                permissions.IsAdminUser
            ]  # Разрешаем только администратору
        elif self.action == "complete":  # Если действие - завершение задачи
            permission_classes = [
                permissions.IsAuthenticated
            ]  # Разрешаем любому аутентифицированному пользователю
        else:  # Для всех остальных действий
            permission_classes = [
                permissions.IsAuthenticated
            ]  # Разрешаем только аутентифицированным пользователям
        return [
            permission() for permission in permission_classes
        ]  # Возвращаем список объектов разрешений

    def perform_create(self, serializer):
        """
        Автоматически устанавливает создателя задачи на текущего пользователя.
        Этот метод вызывается при создании новой задачи.
        """
        logger.info(
            f"Creating task with data: {serializer.validated_data}"
        )  # Добавляем логирование
        serializer.save(
            creator=self.request.user
        )  # Сохраняем информацию о создателе задачи

    def perform_update(self, serializer):
        """
        Автоматически устанавливает обновившего задачу на текущего пользователя.
        Этот метод вызывается при обновлении существующей задачи.
        """
        task = self.get_object()
        logger.info(
            f"Updating task {task.pk} with data: {serializer.validated_data}"
        )  # Добавляем логирование
        serializer.save(
            updater=self.request.user
        )  # Сохраняем информацию об обновившем задачу

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        API endpoint для завершения задачи.
        При POST запросе на этот endpoint задача помечается как завершенная.
        """
        task = self.get_object()  # Получаем объект задачи по ID
        logger.info(f"Completing task {task.pk}")  # Добавляем логирование
        task.status = "completed"  # Устанавливаем статус задачи как "completed"
        task.save()  # Сохраняем изменения в базе данных
        return Response(
            {"status": "task completed"}
        )  # Возвращаем ответ с информацией о завершении задачи

    def get_queryset(self):
        """
        Опционально ограничивает возвращаемые задачи для заданного пользователя.
        Фильтрует задачи по имени пользователя, указанному в параметрах запроса.
        """
        queryset = Task.objects.all()  # Получаем все задачи
        username = self.request.query_params.get(
            "username"
        )  # Получаем имя пользователя из параметров запроса
        if username is not None:  # Если имя пользователя указано
            queryset = queryset.filter(
                creator__email=username
            )  # Фильтруем задачи по email
        return queryset  # Возвращаем отфильтрованный список задач


class BusyEmployeesView(generics.ListAPIView):
    """
    API endpoint для получения списка занятых сотрудников.
    Занятыми считаются сотрудники, у которых больше 5 задач в статусе "new" или "in progress".
    """

    serializer_class = (
        EmployeeSerializer  # Указываем сериализатор для преобразования данных
    )
    permission_classes = [
        permissions.IsAdminUser
    ]  # Разрешаем доступ только администратору

    def get_queryset(self):
        """
        Определяет, какие сотрудники считаются занятыми.
        Используем агрегацию для подсчета количества задач у каждого сотрудника и фильтруем тех, у кого больше 5 задач.
        """
        logger.info("Getting busy employees")  # Добавляем логирование
        # Логика для определения занятых сотрудников
        # Пример: сотрудники, у которых больше 5 задач в статусе "new" или "in progress"
        busy_employees = Employee.objects.annotate(  # Добавляем аннотацию num_tasks к каждому сотруднику
            num_tasks=Count(  # Подсчитываем количество задач
                "tasks",  # Связанных с сотрудником через поле 'tasks'
                filter=Q(
                    tasks__status__in=["new", "in_progress"]
                ),  # Фильтруем задачи по статусу
            )
        ).filter(
            num_tasks__gt=5
        )  # Фильтруем сотрудников, у которых больше 5 задач
        return busy_employees  # Возвращаем список занятых сотрудников


class ImportantTasksView(generics.ListAPIView):
    """
    API endpoint для получения списка важных задач.
    Важными считаются задачи с высоким приоритетом и сроком выполнения менее 7 дней.
    """

    serializer_class = (
        TaskSerializer  # Указываем сериализатор для преобразования данных
    )
    permission_classes = [
        permissions.IsAdminUser
    ]  # Разрешаем доступ только администратору

    def get_queryset(self):
        """
        Определяет, какие задачи считаются важными.
        Фильтруем задачи по приоритету и сроку выполнения.
        """
        logger.info("Getting important tasks")  # Добавляем логирование
        # Логика для определения важных задач
        # Пример: задачи с высоким приоритетом и сроком выполнения менее 7 дней
        important_tasks = (
            Task.objects.filter(  # Фильтруем задачи
                ~Q(status="new"),  # Исключаем новые задачи
                parent_task__status="new",  # У которых есть родительская задача в статусе "новая"
            )
            .order_by("-priority", "deadline")
            .distinct()
        )  # Фильтруем задачи

        return important_tasks  # Возвращаем список важных задач
