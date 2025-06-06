FROM python:3.11-slim

WORKDIR /app

# Обновляем список пакетов и устанавливаем необходимые инструменты сборки
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc python3-dev

# Обновляем pip
RUN python -m pip install --upgrade pip

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY . .

# Команда для запуска приложения
CMD ["gunicorn", "task_tracker.wsgi:application", "--bind", "0.0.0.0:8000"]