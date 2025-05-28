from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Task, Employee
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from unittest.mock import patch
import time

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
        """
        client = APIClient()
        client.force_authenticate(user=self.admin_user)  # Аутентифицируем администратора

        with patch("tasks.tasks.calculate_important_tasks") as mock_task:
            response = client.get("/api/important_tasks/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_task.assert_called_once()


class TaskFilteringAndSearchTests(APITestCase):
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
        self.employee2 = Employee.objects.create(
            full_name="Олег Савченко", position="Менеджер", user=self.admin_user
        )
        self.task = Task.objects.create(
            name="Тестовая задача",
            assignee=self.employee,
            creator=self.admin_user,
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_filter_by_assignee(self):
        """Проверяет фильтрацию задач по assignee."""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        Task.objects.all().delete()
        task1 = Task.objects.create(name="Задача 1", assignee=self.employee, status="new")
        task2 = Task.objects.create(name="Задача 2", assignee=self.employee2, status="in_progress")
        task3 = Task.objects.create(name="Задача 3", assignee=self.employee, status="completed")
        task4 = Task.objects.create(name="Задача 4", assignee=self.employee2, status="new")
        self.assertEqual(task1.name, "Задача 1")
        self.assertEqual(task2.name, "Задача 2")
        self.assertEqual(task3.name, "Задача 3")
        self.assertEqual(task4.name, "Задача 4")

        response = client.get(f"/api/tasks/?assignee={self.employee.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        print(f"Expected assignee: {self.employee.pk}")

        results = response.data['results']
        self.assertEqual(len(results), 2)  # Должно быть 2 задачи

        for task in results:
            print(f"Task assignee: {task['assignee']}")
            self.assertEqual(task["assignee"], self.employee.pk)

    def test_filter_by_creator(self):
        """Проверяет фильтрацию задач по создателю."""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        Task.objects.all().delete()
        task1 = Task.objects.create(name="Задача 1", creator=self.admin_user,
                                    status="new")
        task2 = Task.objects.create(name="Задача 2", creator=self.admin_user,
                                    status="in_progress")
        self.assertEqual(task1.name, "Задача 1")
        self.assertEqual(task2.name, "Задача 2")
        response = client.get(f"/api/tasks/?creator={self.admin_user.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        time.sleep(1)  # Добавьте задержку в 1 секунду
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]["name"], "Задача 1")

    def test_filter_by_status(self):
        """Проверяет фильтрацию задач по статусу."""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        Task.objects.all().delete()
        task1 = Task.objects.create(name="Задача 1", status="new")
        task2 = Task.objects.create(name="Задача 2", status="in_progress")
        self.assertEqual(task1.name, "Задача 1")
        self.assertEqual(task2.name, "Задача 2")

        response = client.get(f'{"/api/tasks/?status=new"}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        for task in response.data['results']:
            print(f"Task status: {task['status']}")

        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]["name"], "Задача 1")

    def test_ordering_by_deadline(self):
        """Проверяет сортировку задач по дедлайну."""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        Task.objects.all().delete()
        # Создаем задачи с разными дедлайнами
        task1 = Task.objects.create(name="Задача 1", status="new", deadline=timezone.now().date() + timedelta(days=2))
        task2 = Task.objects.create(name="Задача 2", status="new", deadline=timezone.now().date())
        task3 = Task.objects.create(name="Задача 3", status="new",
                                    deadline=timezone.now().date() + timedelta(days=1))

        self.assertEqual(task1.name, "Задача 1")
        self.assertEqual(task2.name, "Задача 2")
        self.assertEqual(task3.name, "Задача 3")
        response = client.get(f'{"/api/tasks/?ordering=deadline"}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data['results']
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["name"], "Задача 2")  # Самый ранний deadline
        self.assertEqual(results[1]["name"], "Задача 3")  # Второй по раннему deadline
        self.assertEqual(results[2]["name"], "Задача 1")  # Самый поздний deadline

    def test_search_by_name(self):
        """Проверяет поиск задач по имени."""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        task1 = Task.objects.create(name="Задача 1", status="new", deadline=timezone.now().date())
        task2 = Task.objects.create(name="Задача 2", status="in_progress", deadline=timezone.now().date())
        self.assertEqual(task1.name, "Задача 1")
        self.assertEqual(task2.name, "Задача 2")

        response = client.get(f'{"/api/tasks/?search=Задача 1"}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        print(f"Response data: {response.data}")

        if len(response.data['results']) > 0:
            self.assertEqual(response.data['results'][0]["name"], "Задача 1")
        else:
            self.fail("No results found for search query 'Задача 1'")
