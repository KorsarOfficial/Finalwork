from django.db import models
from django.conf import settings


class Employee(models.Model):
    full_name = models.CharField(
        max_length=100, verbose_name="ФИО", help_text="Укажите ФИО"
    )
    position = models.CharField(
        max_length=100, verbose_name="Должность", help_text="Укажите должность"
    )
    email = models.EmailField(
        blank=True, null=True, verbose_name="Почта", help_text="Укажите почту"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employees",
        verbose_name="Пользователь",
        help_text="Выберите пользователя",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self):
        return self.full_name
