from celery import shared_task
from django.db.models import Count, Q
from .models import Task
from employees.models import Employee


@shared_task
def calculate_important_tasks():
    """
    Асинхронная задача Celery для расчета списка важных задач и определения ответственных сотрудников.

    Логика:
    1.  Определяем важные задачи как задачи, у которых статус "в процессе" или "завершен", и при этом есть родительская задача со статусом "новая".
    2.  Для каждой важной задачи определяем наименее загруженного сотрудника.
    3.  Если наименее загруженный сотрудник не найден (нет сотрудников), назначаем задачу первому попавшемуся сотруднику (если он есть) или сообщаем, что сотрудников нет.
    4.  Если у задачи есть родительская задача, проверяем, не является ли ответственный за родительскую задачу более подходящим кандидатом (с учетом загруженности).
    5.  Сохраняем информацию о задаче и назначенном сотруднике в список результатов.

    Возвращаем:
        list: Список словарей с информацией о важных задачах и назначенных сотрудниках.
              Каждый словарь содержит ключи "task_name", "deadline" и "employee".
    """
    important_tasks = Task.objects.filter(  # Фильтруем задачи
        ~Q(status="new"),  # Исключаем новые задачи
        parent_task__status="new",  # У которых есть родительская задача в статусе "новая"
    ).distinct()  # Убираем дубликаты

    result = []  # Создаем пустой список для результатов

    for task in important_tasks:  # Перебираем важные задачи
        least_loaded_employee = (  # Находим наименее загруженного сотрудника
            Employee.objects.annotate(  # Добавляем аннотацию num_tasks к каждому сотруднику
                num_tasks=Count(  # Подсчитываем количество задач
                    "tasks",  # Связанных с сотрудником через поле 'tasks'
                    filter=Q(
                        tasks__status__in=["new", "in_progress"]
                    ),  # Фильтруем задачи по статусу
                )
            )
            .order_by(
                "num_tasks"
            )  # Сортируем сотрудников по количеству задач (по возрастанию)
            .first()  # Берем первого сотрудника (с наименьшим количеством задач)
        )

        if (
            not least_loaded_employee
        ):  # Если наименее загруженный сотрудник не найден (нет сотрудников)
            available_employees = Employee.objects.all()  # Получаем всех сотрудников
            if available_employees.count() == 0:  # Если сотрудников нет
                available_employee_name = (
                    "Сотрудников нет"  # Сообщаем, что сотрудников нет
                )
            else:  # Если сотрудники есть
                available_employee = (
                    available_employees.first()
                )  # Берем первого попавшегося сотрудника
                available_employee_name = (
                    available_employee.full_name
                )  # Получаем его имя

            result.append(  # Добавляем информацию о задаче и отсутствии сотрудника в список результатов
                {
                    "task_name": task.name,  # Имя задачи
                    "deadline": task.deadline,  # Срок выполнения
                    "employee": available_employee_name,  # Имя сотрудника ("Сотрудников нет" или имя первого попавшегося сотрудника)
                }
            )
            continue  # Переходим к следующей задаче

        parent_task_assignee = None  # Инициализируем переменную для хранения ответственного за родительскую задачу
        if task.parent_task:  # Если у задачи есть родительская задача
            parent_task_assignee = (
                task.parent_task.assignee
            )  # Получаем ответственного за родительскую задачу

        assignee = least_loaded_employee  # Изначально назначаем задачу наименее загруженному сотруднику
        if (
            parent_task_assignee
            and (  # Если есть ответственный за родительскую задачу и
                parent_task_assignee.tasks.filter(
                    status__in=["new", "in_progress"]
                ).count()  # Количество задач у ответственного за родительскую задачу
                <= least_loaded_employee.tasks.filter(  # Меньше или равно
                    status__in=[
                        "new",
                        "in_progress",
                    ]  # Количество задач у наименее загруженного сотрудника
                ).count()
                + 2  # Плюс 2 (небольшая погрешность)
            )
        ):
            assignee = parent_task_assignee  # Назначаем задачу ответственному за родительскую задачу
        elif not parent_task_assignee:  # Если нет ответственного за родительскую задачу
            assignee = least_loaded_employee  # Назначаем задачу наименее загруженному сотруднику

        result.append(  # Добавляем информацию о задаче и назначенном сотруднике в список результатов
            {
                "task_name": task.name,  # Имя задачи
                "deadline": task.deadline,  # Срок выполнения
                "employee": assignee.full_name,  # Имя назначенного сотрудника
            }
        )
    return result  # Возвращаем список результатов
