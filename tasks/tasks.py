from celery import shared_task
from django.db.models import Count, Q
from .models import Task
from employees.models import Employee


@shared_task
def calculate_important_tasks():
    """
    Асинхронная задача Celery для расчета списка важных задач и определения ответственных сотрудников.

    Логика:
    1.  Определяем важные задачи как задачи,
    у которых статус "в процессе" или "завершен",
    и при этом есть родительская задача со статусом "новая".
    2.  Для каждой важной задачи определяем наименее
    загруженного сотрудника.
    3.  Если наименее загруженный сотрудник не найден
    (нет сотрудников), назначаем задачу первому попавшемуся
    сотруднику (если он есть) или сообщаем, что сотрудников нет.
    4.  Если у задачи есть родительская задача, проверяем,
    не является ли ответственный за родительскую задачу
    более подходящим кандидатом (с учетом загруженности).
    5.  Сохраняем информацию о задаче и назначенном сотруднике
    в список результатов.

    Возвращаем:
        list: Список словарей с информацией о важных
        задачах и назначенных сотрудниках.
              Каждый словарь содержит ключи "task_name",
               "deadline" и "employee".
    """
    important_tasks = Task.objects.filter(  # Фильтруем задачи
        ~Q(status="new"),  # Исключаем новые задачи
        parent_task__status="new",  # У которых есть родительская задача в статусе "новая"
    ).distinct()  # Убираем дубликаты

    result = []  # Создаем пустой список для результатов

    for task in important_tasks:
        least_loaded_employee = (  # Находим наименее загруженного сотрудника
            Employee.objects.annotate(  # Добавляем аннотацию num_tasks к каждому сотруднику
                num_tasks=Count(  # Подсчитываем количество задач
                    "tasks", filter=Q(tasks__status__in=["new", "in_progress"])
                    # Связанных с сотрудником через поле 'tasks'
                    # Фильтруем задачи по статусу
                )
            )
            .order_by("num_tasks")  # Сортируем сотрудников по количеству задач (по возрастанию)
            .first()  # Берем первого сотрудника (с наименьшим количеством задач)
        )

        if not least_loaded_employee:  # Если наименее загруженный сотрудник не найден (нет сотрудников)
            available_employees = Employee.objects.all()
            if available_employees.count() == 0:
                result.append({"task_name": task.name, "deadline": task.deadline, "employee": "Сотрудников нет"})
            else:
                available_employee = available_employees.first()  # Берем первого попавшегося сотрудника
                result.append(
                    {"task_name": task.name, "deadline": task.deadline, "employee": available_employee.full_name})
            continue

        assignee = least_loaded_employee

        if task.parent_task and task.parent_task.assignee:  # Если есть ответственный за родительскую задачу
            parent_task_assignee = task.parent_task.assignee

            if (
                    parent_task_assignee.tasks.filter(status__in=["new", "in_progress"]).count()
                    <= least_loaded_employee.tasks.filter(status__in=["new", "in_progress"]).count() + 2
            ):
                assignee = parent_task_assignee  # Назначаем задачу ответственному за родительскую задачу

        result.append({"task_name": task.name, "deadline": task.deadline, "employee": assignee.full_name})

    return result
