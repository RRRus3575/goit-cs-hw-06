FROM python:3.9-slim

# Встановлення залежностей
RUN pip install pymongo

# Копіювання всіх файлів до контейнера
COPY . /app

# Встановлення робочої директорії
WORKDIR /app

# Команда для запуску
CMD ["python", "main.py"]


