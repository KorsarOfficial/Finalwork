import django_filters
from .models import Task


class TaskFilter(django_filters.FilterSet):
    """
    Фильтр для задач.
    Позволяет фильтровать задачи по различным параметрам,
    таким как имя, статус, назначенный сотрудник,
    приоритет и срок выполнения.
    """

    name = django_filters.CharFilter(
        lookup_expr="icontains",
        help_text="Фильтрация по имени задачи (регистронезависимый поиск)",
    )
    """
        Фильтр по имени задачи (регистронезависимый поиск).
        Использует lookup_expr="icontains" для поиска задач, содержащих указанное значение в имени.
    """
    status = django_filters.ChoiceFilter(
        choices=Task.STATUS_CHOICES,
        help_text="Фильтрация по статусу задачи (новый, в процессе, завершен)",
    )
    """
        Фильтр по статусу задачи.
        Использует choices=Task.STATUS_CHOICES для выбора статуса из предопределенного списка.
    """
    assignee = django_filters.NumberFilter(
        field_name="assignee__id", help_text="Фильтрация по ID назначенного сотрудника"
    )
    """
        Фильтр по ID назначенного сотрудника.
        Использует field_name="assignee__id" для фильтрации по ID связанной модели Employee.
    """
    priority__gt = django_filters.NumberFilter(
        field_name="priority",
        lookup_expr="gt",
        help_text="Фильтрация по приоритету задачи (больше, чем)",
    )
    """
        Фильтр по приоритету задачи (больше, чем).
        Использует lookup_expr="gt" для фильтрации задач с приоритетом больше указанного значения.
    """
    priority__lt = django_filters.NumberFilter(
        field_name="priority",
        lookup_expr="lt",
        help_text="Фильтрация по приоритету задачи (меньше, чем)",
    )
    """
        Фильтр по приоритету задачи (меньше, чем).
        Использует lookup_expr="lt" для фильтрации задач с приоритетом меньше указанного значения.
    """
    deadline__gt = django_filters.DateFilter(
        field_name="deadline",
        lookup_expr="gt",
        help_text="Фильтрация по сроку выполнения задачи (позже, чем)",
    )
    """
        Фильтр по сроку выполнения задачи (позже, чем).
        Использует lookup_expr="gt" для фильтрации задач со сроком выполнения позже указанной даты.
    """
    deadline__lt = django_filters.DateFilter(
        field_name="deadline",
        lookup_expr="lt",
        help_text="Фильтрация по сроку выполнения задачи (раньше, чем)",
    )
    """
        Фильтр по сроку выполнения задачи (раньше, чем).
        Использует lookup_expr="lt" для фильтрации задач со сроком выполнения раньше указанной даты.
    """

    class Meta:
        """
        Метаданные для фильтра.
        Определяют модель, для которой создается фильтр,
        и список полей, по которым можно фильтровать.
        """

        model = Task
        fields = [
            "name",
            "status",
            "assignee",
            "priority",
            "deadline",
        ]
        """
            Список полей, по которым можно фильтровать задачи.
            Соответствует полям, определенным в модели Task.
        """
