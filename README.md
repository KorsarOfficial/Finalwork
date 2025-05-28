# Task Tracker API

## Обзор

Этот проект представляет собой API для управления задачами сотрудников. Он позволяет создавать, читать, обновлять и удалять сотрудников и задачи, а также предоставляет специальные endpoints для получения информации о загруженности сотрудников и важных задачах.

## Пакеты

*   Python 3.11
*   Django 5.2.1
*   Django REST Framework 3.16.0
*   PostgreSQL 15
*   Celery 5.5.2
*   Redis 6.1.0
*   Docker
*   drf-yasg 1.21.10

## Установка

1.  Клонируйте репозиторий:

    ```
    git clone https://github.com/Seriynaya/Finalwork
    ```

2.  Создайте виртуальное окружение:

    ```
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate  # Windows
    ```

3.  Установите зависимости:

    ```
    pip install -r requirements.txt
    ```

4.  Создайте файл `.env` в корне проекта и настройте переменные окружения:

    ```
    DJANGO_SECRET_KEY=your_secret_key
    DJANGO_DEBUG=True
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=5432
    POSTGRES_DB=finalwork
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0
    REDIS_URL=redis://redis:6379/1
    ```

5.  Примените миграции:

    ```
    python manage.py migrate
    ```

## Запуск проекта

1.  Запустите проект с использованием Docker Compose:

    ```
    docker-compose up --build
    ```

    Этот запуск создаст контейнеры для Django, PostgreSQL, Redis и Celery worker.

2.  После запуска проекта вы можете получить доступ к:

    *   Приложению: [http://localhost:8000](http://localhost:8000)
    *   Swagger UI: [http://localhost:8000/swagger/](http://localhost:8000/swagger/) - документация API.
    *   Redis: `redis-cli -h localhost -p 6379`

## Описание API

API предоставляет следующие endpoints:

*   `/api/employees/`: CRUD для сотрудников. Требуется аутентификация администратора для создания, обновления и удаления.
*   `/api/tasks/`: CRUD для задач. Требуется аутентификация администратора для создания, обновления и удаления. Назначенный пользователь или администратор может просматривать задачу.
*   `/api/tasks/busy_employees/`: Список занятых сотрудников. Требуется аутентификация администратора.
*   `/api/tasks/important_tasks/`: Список важных задач. Требуется аутентификация администратора.
*   `/api/users/`: Список пользователей.

Подробное описание API доступно в Swagger UI: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)


## Структура проекта

1. employees - приложение для управления сотрудниками.
2. tasks - приложение для управления задачами.
3. users - приложение для работы с пользователями.
4. .github/workflows/main.yml - папка GitHub Actions для автоматизации задача.
5. monitoring.py - скрипт мониторинга, который проверяет доступность API по указанному URL.


## Запуск тестов
Для запуска тестов выполните следующие команды:
```
coverage run manage.py test
coverage report -m
coverage html #для генерации html отчета
```