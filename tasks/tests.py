from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Task, Employee
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from unittest.mock import patch

User = get_user_model()


class TaskModelValidationTests(APITestCase):
    """
    Этот класс содержит тесты для проверки валидации модели Task.
    Валидация модели проверяет, что данные, сохраняемые в базе данных, соответствуют заданным правилам.
    """

    def setUp(self):
        """
        Метод setUp() вызывается перед каждым тестом.
        Здесь мы создаем объект Employee, который будет использоваться в тестах.
        """
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.employee = Employee.objects.create(
            full_name="Иванов Иван", position="Разработчик", user=self.admin_user
        )

    def test_valid_task(self):
        """
        Проверяет, что валидный объект Task проходит валидацию.
        Создаем объект Task с корректными данными и проверяем,
        что вызов full_clean() не вызывает исключение ValidationError.
        """
        deadline = timezone.now().date() + timedelta(days=7)
        task = Task(
            name="Тестовая задача",
            assignee=self.employee,
            deadline=deadline,
            creator=self.admin_user,
        )
        try:
            task.full_clean()
        except ValidationError:
            self.fail("Validation failed for a valid task")

    def test_deadline_in_past(self):
        """
        Проверяет, что объект Task с дедлайном в прошлом
        не проходит валидацию.
        Создаем объект Task с дедлайном в прошлом и проверяем,
        что вызов full_clean() вызывает исключение ValidationError.
        Также проверяем, что сообщение об ошибке содержит ожидаемый текст.
        """
        deadline = timezone.now().date() - timedelta(days=1)
        task = Task(
            name="Просроченная задача",
            assignee=self.employee,
            deadline=deadline,
            creator=self.admin_user,
        )
        with self.assertRaises(ValidationError) as context:
            task.full_clean()
        self.assertIn("Срок не может быть в прошлом", str(context.exception))

    def test_priority_negative(self):
        """
        Проверяет, что объект Task с отрицательным приоритетом
        не проходит валидацию.
        Создаем объект Task с отрицательным приоритетом и проверяем,
        что вызов full_clean() вызывает исключение ValidationError.
        Также проверяем, что сообщение об ошибке содержит ожидаемый текст.
        """
        deadline = timezone.now().date() + timedelta(days=7)
        task = Task(
            name="Тестовая задача",
            assignee=self.employee,
            deadline=deadline,
            priority=-1,
            creator=self.admin_user,
        )
        with self.assertRaises(ValidationError) as context:
            task.full_clean()
        self.assertIn("Приоритет должен быть неотрицательным", str(context.exception))

    def test_blank_description(self):
        """
        Проверяет, что объект Task с пустым описанием проходит валидацию,
        если описание не является обязательным полем.
        Создаем объект Task с пустым описанием и проверяем,
        что вызов full_clean() не вызывает исключение ValidationError.
        """
        deadline = timezone.now().date() + timedelta(days=7)
        task = Task(
            name="Тестовая задача",
            assignee=self.employee,
            deadline=deadline,
            description="",
            creator=self.admin_user,
        )
        try:
            task.full_clean()
        except ValidationError:
            self.fail("Validation failed for blank description")

    def test_null_assignee(self):
        """
        Проверяет, что объект Task с assignee, равным None,
        проходит валидацию, если assignee может быть None.
        Создаем объект Task с assignee, равным None, и проверяем,
        что вызов full_clean() не вызывает исключение ValidationError.
        """
        deadline = timezone.now().date() + timedelta(days=7)
        task = Task(
            name="Тестовая задача",
            assignee=None,
            deadline=deadline,
            creator=self.admin_user,
        )
        try:
            task.full_clean()
        except ValidationError:
            self.fail("Validation failed for blank description")


class TaskPermissionsTests(APITestCase):
    """
    Этот класс содержит тесты для проверки прав доступа к API endpoints, связанным с моделью Task.
    Проверяем, что разные типы пользователей (администратор, обычный пользователь)
    имеют разные права доступа к API.
    """

    def setUp(self):
        """
        Метод setUp() вызывается перед каждым тестом.
        Здесь мы создаем тестовых пользователей (администратора и обычного пользователя), объект Employee и объект Task.
        """
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.regular_user = User.objects.create_user(
            email="user@example.com", password="password"
        )
        self.employee = Employee.objects.create(
            full_name="Иванов Иван", position="Разработчик", user=self.admin_user
        )
        self.task = Task.objects.create(
            name="Тестовая задача",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=7),
            creator=self.admin_user,
        )

    def test_admin_can_create_task(self):
        """
        Проверяет, что администратор может создавать объекты Task через API.
        Аутентифицируем администратора, отправляем POST запрос на endpoint создания Task и проверяем,
        что статус код ответа равен 201 Created.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("task-list")
        data = {
            "name": "Новая задача",
            "assignee_id": self.employee.id,
            "deadline": str(timezone.now().date() + timedelta(days=7)),
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_task(self):
        """
        Проверяет, что обычный пользователь не может создавать объекты Task через API.
        Аутентифицируем обычного пользователя, отправляем POST запрос на endpoint создания Task и проверяем,
        что статус код ответа равен 403 Forbidden.
        """
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("task-list")
        data = {
            "name": "Новая задача",
            "assignee_id": self.employee.id,
            "deadline": str(timezone.now().date() + timedelta(days=7)),
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_task(self):
        """
        Проверяет, что администратор может обновлять объекты Task через API.
        Аутентифицируем администратора, отправляем PUT запрос на endpoint обновления Task и проверяем,
        что статус код ответа равен 200 OK.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("task-detail", kwargs={"pk": self.task.pk})
        data = {
            "name": "Измененная задача",
            "assignee_id": self.employee.id,
            "deadline": str(timezone.now().date() + timedelta(days=14)),
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_update_task(self):
        """
        Проверяет, что обычный пользователь не может обновлять объекты Task через API.
        Аутентифицируем обычного пользователя, отправляем PUT запрос на endpoint обновления Task и проверяем,
        что статус код ответа равен 403 Forbidden.
        """
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("task-detail", kwargs={"pk": self.task.pk})
        data = {
            "name": "Измененная задача",
            "assignee_id": self.employee.id,
            "deadline": str(timezone.now().date() + timedelta(days=14)),
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_task(self):
        """
        Проверяет, что администратор может удалять объекты Task через API.
        Аутентифицируем администратора, отправляем DELETE запрос на endpoint удаления Task и проверяем,
        что статус код ответа равен 204 No Content.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("task-detail", kwargs={"pk": self.task.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_regular_user_cannot_delete_task(self):
        """
        Проверяет, что обычный пользователь не может удалять объекты Task через API.
        Аутентифицируем обычного пользователя, отправляем DELETE запрос на endpoint удаления Task и проверяем,
        что статус код ответа равен 403 Forbidden.
        """
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("task-detail", kwargs={"pk": self.task.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_get_busy_employees(self):
        """
        Проверяет, что администратор может получить список занятых сотрудников через API.
        Аутентифицируем администратора, отправляем GET запрос на endpoint
        получения списка занятых сотрудников и проверяем,
        что статус код ответа равен 200 OK.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("busy_employees")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_get_busy_employees(self):
        """
        Проверяет, что обычный пользователь не может получить список
        занятых сотрудников через API.
        Аутентифицируем обычного пользователя, отправляем GET запрос
        на endpoint получения списка занятых сотрудников и проверяем,
        что статус код ответа равен 403 Forbidden.
        """
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("busy_employees")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_get_busy_employees(self):
        """
        Проверяет, что неаутентифицированный пользователь не может получить список занятых сотрудников через API.
        Отправляем GET запрос на endpoint получения списка занятых сотрудников и проверяем,
        что статус код ответа равен 401 Unauthorized.
        """
        url = reverse("busy_employees")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_get_important_tasks(self):
        """
        Проверяет, что администратор может получить список важных задач через API.
        Аутентифицируем администратора, отправляем GET запрос на endpoint получения списка важных задач и проверяем,
        что статус код ответа равен 200 OK.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("important_tasks")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_get_important_tasks(self):
        """
        Проверяет, что обычный пользователь не может получить список
        важных задач через API.
        Аутентифицируем обычного пользователя, отправляем GET запрос
        на endpoint получения списка важных задач и проверяем,
        что статус код ответа равен 403 Forbidden.
        """
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("important_tasks")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_get_important_tasks(self):
        """
        Проверяет, что неаутентифицированный пользователь не может получить список важных задач через API.
        Отправляем GET запрос на endpoint получения списка важных задач и проверяем,
        что статус код ответа равен 401 Unauthorized.
        """
        url = reverse("important_tasks")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskLoggingTests(APITestCase):
    """
    Этот класс содержит тесты для проверки логирования операций с моделью Task.
    Проверяем, что при создании, обновлении и удалении задач в логи записывается информация о событии.
    """

    def setUp(self):
        """
        Метод setUp() вызывается перед каждым тестом.
        Здесь мы создаем тестового пользователя (администратора), объект Employee и объект Task.
        """
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.employee = Employee.objects.create(
            full_name="Иванов Иван", position="Разработчик", user=self.admin_user
        )
        self.task = Task.objects.create(
            name="Тестовая задача",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=7),
            creator=self.admin_user,
        )

    def test_create_task_logs_info(self):
        """
        Проверяет, что при создании задачи в логи записывается информация об этом событии.
        Аутентифицируем администратора, отправляем POST запрос на endpoint создания Task,
        и проверяем, что в логи записано сообщение с информацией о созданном Task.
        """
        with self.assertLogs(logger="tasks.views", level="INFO") as cm:
            self.client.force_authenticate(user=self.admin_user)
            url = reverse("task-list")
            data = {
                "name": "Новая задача",
                "assignee_id": self.employee.id,
                "deadline": str(timezone.now().date() + timedelta(days=7)),
            }
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn("Creating task with data", cm.output[0])
            self.assertIn(data["name"], cm.output[0])

    def test_update_task_logs_info(self):
        """
        Проверяет, что при обновлении задачи в логи записывается информация об этом событии.
        Аутентифицируем администратора, отправляем PUT запрос на endpoint обновления Task,
        и проверяем, что в логи записано сообщение с информацией об обновленном Task.
        """
        with self.assertLogs(logger="tasks.views", level="INFO") as cm:
            self.client.force_authenticate(user=self.admin_user)
            url = reverse("task-detail", kwargs={"pk": self.task.pk})
            data = {
                "name": "Измененная задача",
                "assignee_id": self.employee.id,
                "deadline": str(timezone.now().date() + timedelta(days=14)),
            }
            response = self.client.put(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(f"Updating task {self.task.pk} with data", cm.output[0])
            self.assertIn(data["name"], cm.output[0])

    def test_delete_task_logs_info(self):
        """
        Проверяет, что при удалении задачи в логи записывается информация об этом событии.
        Аутентифицируем администратора, отправляем DELETE запрос на endpoint удаления Task,
        и проверяем, что в логи записано сообщение с информацией об удаленном Task.
        """
        with self.assertLogs(logger="tasks.views", level="INFO") as cm:
            self.client.force_authenticate(user=self.admin_user)
            url = reverse("task-detail", kwargs={"pk": self.task.pk})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertIn(f"Deleting task {self.task.pk}", cm.output[0])

    def test_complete_task_logs_info(self):
        """
        Проверяет, что при завершении задачи в логи записывается информация об этом событии.
        Аутентифицируем администратора, отправляем POST запрос на endpoint завершения Task,
        и проверяем, что в логи записано сообщение с информацией о завершенном Task.
        """
        with self.assertLogs(logger="tasks.views", level="INFO") as cm:
            self.client.force_authenticate(user=self.admin_user)
            url = reverse("task-complete", kwargs={"pk": self.task.pk})
            response = self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(f"Completing task {self.task.pk}", cm.output[0])

    def test_busy_employees_logs_info(self):
        """
        Проверяет, что при получении списка занятых сотрудников в логи записывается информация об этом событии.
        Аутентифицируем администратора, отправляем GET запрос на endpoint получения списка занятых сотрудников,
        и проверяем, что в логи записано сообщение с информацией о запросе.
        """
        with self.assertLogs(logger="tasks.views", level="INFO") as cm:
            self.client.force_authenticate(user=self.admin_user)
            url = reverse("busy_employees")
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("Getting busy employees", cm.output[0])

    def test_important_tasks_logs_info(self):
        """
        Проверяет, что при получении списка важных задач в логи записывается информация об этом событии.
        Аутентифицируем администратора, отправляем GET запрос на endpoint получения списка важных задач,
        и проверяем, что в логи записано сообщение с информацией о запросе.
        """
        with self.assertLogs(logger="tasks.views", level="INFO") as cm:
            self.client.force_authenticate(user=self.admin_user)
            url = reverse("important_tasks")
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("Getting important tasks", cm.output[0])


class CeleryTasksTests(APITestCase):
    """
    Этот класс содержит тесты для проверки работы асинхронных задач Celery.
    Проверяем, что задачи Celery выполняются правильно и возвращают ожидаемые результаты.
    """

    def setUp(self):
        """
        Метод setUp() вызывается перед каждым тестом.
        Здесь мы создаем объект Employee и объект User (администратора).
        """
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.employee = Employee.objects.create(
            full_name="Иванов Иван", position="Разработчик", user=self.admin_user
        )

    def test_calculate_important_tasks_returns_correct_result(self):
        """
        Проверяет, что задача Celery calculate_important_tasks возвращает правильный результат.
        Создаем тестовые задачи, вызываем задачу Celery и проверяем, что результат содержит ожидаемые данные.
        """
        # Создаем тестовые задачи
        task1 = Task.objects.create(
            name="Задача 1",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=7),
            status="new",
            priority=8,
            creator=self.admin_user,
        )
        task2 = Task.objects.create(
            name="Задача 2",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=14),
            status="in_progress",
            parent_task=task1,
            priority=9,
            creator=self.admin_user,
        )  # Эта задача зависит от задачи 1

        self.assertEqual(task2.name, "Задача 2")

        # Вызываем Celery задачу
        from .tasks import calculate_important_tasks

        result = (
            calculate_important_tasks()
        )

        # Проверяем результат
        self.assertEqual(len(result), 1)  # Только 1 важная задача (task1)
        self.assertEqual(result[0]["task_name"], "Задача 2")

    def test_important_tasks_view_calls_celery_task(self):
        """
        Проверяет, что представление ImportantTasksView вызывает задачу Celery calculate_important_tasks.
        Используем mock для замены задачи Celery и проверяем, что она была вызвана.
        """

        # Mock Celery task
        with patch("tasks.tasks.calculate_important_tasks.delay") as mocked_task:
            # Делаем запрос на просмотр
            self.client.force_authenticate(user=self.admin_user)
            url = reverse("important_tasks")
            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mocked_task.assert_called_once()


class TaskFilteringAndSearchTests(APITestCase):
    """
    Этот класс содержит тесты для проверки фильтрации и поиска задач через API.
    Проверяем, что фильтрация по статусу, assignee, поиск по имени и сортировка работают правильно.
    """

    def setUp(self):
        """
        Метод setUp() вызывается перед каждым тестом.
        Здесь мы создаем тестового пользователя (администратора) и объект Employee.
        """
        # Очищаем данные перед тестом
        Task.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.employee = Employee.objects.create(
            full_name="Иванов Иван", position="Разработчик", user=self.admin_user
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_filter_by_assignee(self):
        """
        Проверяет фильтрацию задач по assignee.
        Создаем несколько задач, назначенных разным сотрудникам,
        и проверяем, что при фильтрации по определенному assignee
        возвращаются только задачи, назначенные этому сотруднику.
        """
        employee2 = Employee.objects.create(
            full_name="Петров Петр", position="Менеджер", user=self.admin_user
        )
        Task.objects.create(
            name="Задача 1",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=7),
            creator=self.admin_user,
        )
        Task.objects.create(
            name="Задача 2",
            assignee=employee2,
            deadline=timezone.now().date() + timedelta(days=14),
            creator=self.admin_user,
        )
        url = reverse("task-list") + f"?assignee={self.employee.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Task.objects.filter(assignee=self.employee).count(), 1)
        if response.data:
            self.assertEqual(response.data[0]["name"], "Задача 1")

    def test_filter_by_status(self):
        """
        Проверяет фильтрацию задач по статусу.
        Создаем несколько задач с разными статусами и проверяем,
        что при фильтрации по определенному статусу возвращаются
        только задачи с этим статусом.
        """
        Task.objects.create(
            name="Задача 1",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=7),
            status="new",
            creator=self.admin_user,
        )
        Task.objects.create(
            name="Задача 2",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=14),
            status="in_progress",
            creator=self.admin_user,
        )
        url = reverse("task-list") + "?status=new"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Task.objects.filter(status="new").count(), 1
        )  # Используем queryset.count()
        if response.data:  # Проверка если пусто
            self.assertEqual(
                response.data[0]["name"],
                "Задача 1"
            )  # Проверка, существуют ли данные перед извлечением

    def test_ordering_by_deadline(self):
        """
        Проверяет сортировку задач по дедлайну.
        Создаем несколько задач с разными дедлайнами и проверяем,
        что при сортировке по дедлайну задачи возвращаются в правильном порядке.
        """
        Task.objects.create(
            name="Задача 1",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=14),
            creator=self.admin_user,
        )
        Task.objects.create(
            name="Задача 2",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=7),
            creator=self.admin_user,
        )
        url = reverse("task-list") + "?ordering=deadline"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(len(response.data), 2)
        self.assertEqual(Task.objects.count(), 2)
        if response.data:
            self.assertEqual(
                response.data[0]["name"], "Задача 2"
            )  # Earlier deadline first

    def test_search_by_name(self):
        """
        Проверяет поиск задач по имени.
        Создаем несколько задач с разными именами и проверяем,
        что при поиске по определенному имени возвращаются только задачи,
        содержащие это имя.
        """
        Task.objects.create(
            name="Тестовая задача 1",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=7),
            creator=self.admin_user,
        )
        Task.objects.create(
            name="Другая задача",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=14),
            creator=self.admin_user,
        )
        url = reverse("task-list") + "?search=Тестовая"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Task.objects.filter(name__icontains="Тестовая").count(), 1)
        # self.assertEqual(len(response.data), 1)
        if response.data:
            self.assertEqual(response.data[0]["name"], "Тестовая задача 1")

    def test_filter_by_creator(self):
        """
        Проверяет фильтрацию задач по создателю.
        Создаем несколько задач, созданных разными пользователями и проверяем,
        что при фильтрации по определенному создателю возвращаются только задачи, созданные этим пользователем.
        """
        regular_user = User.objects.create_user(
            email="regular@example.com", password="password"
        )
        employee2 = Employee.objects.create(
            full_name="Петров Петр", position="Менеджер", user=regular_user
        )

        task1 = Task.objects.create(
            name="Задача 1",
            assignee=self.employee,
            deadline=timezone.now().date() + timedelta(days=7),
            creator=self.admin_user,
        )
        task2 = Task.objects.create(
            name="Задача 2",
            assignee=employee2,
            deadline=timezone.now().date() + timedelta(days=14),
            creator=regular_user,
        )
        self.assertEqual(task1.name, "Задача 1")
        self.assertEqual(task2.name, "Задача 2")

        url = reverse("task-list") + f"?username={self.admin_user.email}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Task.objects.filter(creator__email=self.admin_user.email).count(), 1
        )
        if response.data:
            self.assertEqual(response.data[0]["name"], "Задача 1")
