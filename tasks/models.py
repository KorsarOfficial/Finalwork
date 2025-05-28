from django.db import models
from django.utils import timezone
from employees.models import Employee
from django.conf import settings
from django.core.validators import ValidationError


class Task(models.Model):
    STATUS_CHOICES = [
        ("new", "Новая"),
        ("in_progress", "В процессе"),
        ("completed", "Завершена"),
    ]

    name = models.CharField(
        max_length=200, verbose_name="Название", help_text="Укажите название задачи"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
        help_text="Укажите описание задачи",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name="Статус задачи",
        help_text="Укажите статус задачи",
    )
    assignee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Назначен",
        help_text="Выберите сотрудника, которому назначена задача",
    )
    deadline = models.DateField(
        verbose_name="Срок", help_text="Укажите срок выполнения задачи"
    )
    priority = models.IntegerField(
        default=5, verbose_name="Приоритет", help_text="Укажите приоритет задачи"
    )
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_tasks",
        verbose_name="Родительская задача",
        help_text="Выберите родительскую задачу",
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
        verbose_name="Создатель",
        help_text="Пользователь, создавший задачу",
    )
    updater = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_tasks",
        verbose_name="Обновил",
        help_text="Пользователь, обновивший задачу",
    )

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self):
        return self.name

    def clean(self):
        """
        Валидация модели.
        Срок не может быть в прошлом.
        Приоритет не может быть отрицательным.
        """
        if self.deadline and self.deadline < timezone.now().date():
            raise ValidationError({"deadline": "Срок не может быть в прошлом"})
        if self.priority and self.priority < 0:
            raise ValidationError({"priority": "Приоритет должен быть неотрицательным"})
