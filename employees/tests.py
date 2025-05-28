from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from .models import Employee
from django.core.exceptions import ValidationError

User = get_user_model()


class EmployeeModelValidationTests(APITestCase):
    """
    Этот класс содержит тесты для проверки валидации модели Employee.
    Валидация модели проверяет, что данные, сохраняемые в базе данных, соответствуют заданным правилам.
    """

    def setUp(self):
        """
        Метод setUp() вызывается перед каждым тестом.
        Здесь мы создаем тестового пользователя (администратора), который будет использоваться в тестах.
        """
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )

    def test_valid_employee(self):
        """
        Проверяет, что валидный объект Employee проходит валидацию.
        Создаем объект Employee с корректными данными и проверяем,
        что вызов full_clean() не вызывает исключение ValidationError.
        """
        employee = Employee(
            full_name="Иванов Иван",
            position="Разработчик",
            email="ivan@example.com",
            user=self.admin_user,
        )
        try:
            employee.full_clean()
        except ValidationError:
            self.fail("Validation failed for a valid employee")

    def test_invalid_email(self):
        """
        Проверяет, что объект Employee с некорректным email
        не проходит валидацию.
        Создаем объект Employee с некорректным email и проверяем,
        что вызов full_clean() вызывает исключение ValidationError.
        Также проверяем, что сообщение об ошибке содержит ожидаемый текст.
        """
        employee = Employee(
            full_name="Иванов Иван",
            position="Разработчик",
            email="invalid-email",
            user=self.admin_user,
        )
        with self.assertRaises(ValidationError) as context:
            employee.full_clean()
        self.assertIn(
            "Введите правильный адрес электронной почты.", str(context.exception)
        )

    def test_blank_email(self):
        """
        Проверяет, что объект Employee с пустым email проходит валидацию,
        если email не является обязательным полем.
        Создаем объект Employee с пустым email и проверяем,
        что вызов full_clean() не вызывает исключение ValidationError.
        """
        employee = Employee(
            full_name="Иванов Иван",
            position="Разработчик",
            email="",
            user=self.admin_user,
        )
        try:
            employee.full_clean()
        except ValidationError:
            self.fail("Validation failed for blank email")

    def test_null_email(self):
        """
        Проверяет, что объект Employee с email, равным None,
        проходит валидацию, если email может быть None.
        Создаем объект Employee с email, равным None,
        и проверяем, что вызов full_clean() не вызывает исключение
        ValidationError.
        """
        employee = Employee(
            full_name="Иванов Иван",
            position="Разработчик",
            email=None,
            user=self.admin_user,
        )
        try:
            employee.full_clean()
        except ValidationError:
            self.fail("Validation failed for null email")


class EmployeePermissionsTests(APITestCase):
    """
    Этот класс содержит тесты для проверки прав доступа к API endpoints, связанным с моделью Employee.
    Проверяем, что разные типы пользователей (администратор, обычный пользователь, неаутентифицированный пользователь)
    имеют разные права доступа к API.
    """

    def setUp(self):
        """
        Метод setUp() вызывается перед каждым тестом.
        Здесь мы создаем тестовых пользователей (администратора и обычного пользователя) и объект Employee.
        """
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="password"
        )
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="password"
        )
        self.employee = Employee.objects.create(
            full_name="Иванов Иван",
            position="Разработчик", user=self.admin_user
        )

    def test_admin_can_create_employee(self):
        """
        Проверяет, что администратор может создавать объекты
        Employee через API.
        Аутентифицируем администратора, отправляем POST запрос
        на endpoint создания Employee и проверяем, что статус код
        ответа равен 201 Created.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("employee-list")
        data = {
            "full_name": "Сидоров",
            "position": "Тестировщик",
            "user": self.admin_user.id,
            "email": "test@test.com",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_employee(self):
        """
        Проверяет, что обычный пользователь не может создавать
        объекты Employee через API.
        Аутентифицируем обычного пользователя, отправляем POST
        запрос на endpoint создания Employee и проверяем,
        что статус код ответа равен 403 Forbidden.
        """
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("employee-list")
        data = {
            "full_name": "Сидоров",
            "position": "Тестировщик",
            "user": self.regular_user.id,
            "email": "test@test.com",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_can_view_employee_list(self):
        """
        Проверяет, что аутентифицированный пользователь может
        просматривать список сотрудников.
        Аутентифицируем обычного пользователя, отправляем GET запрос
        на endpoint получения списка сотрудников и проверяем,
        что статус код ответа равен 200 OK.
        """
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("employee-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_can_view_employee_list(self):
        """
        Проверяет, что неаутентифицированный пользователь может просматривать список сотрудников.
        Отправляем GET запрос на endpoint получения списка сотрудников и проверяем,
        что статус код ответа равен 401 Unauthorized.
        """
        url = reverse("employee-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
