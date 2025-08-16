
FROM python:3.11-slim

WORKDIR /app

# Установить системные зависимости для сборки (включая curl для healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        rustc \
        cargo \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . /app

# Проверяем доступность LLM сервера перед запуском
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s \
    CMD curl -f http://llm-server:8001 || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]