FROM ubuntu:22.04

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    git build-essential cmake wget curl libcurl4-openssl-dev

# Клонируем последнюю версию llama.cpp
RUN git clone https://github.com/ggerganov/llama.cpp.git /llama.cpp

# Сборка сервера
WORKDIR /llama.cpp
RUN mkdir -p build && cd build && \
    cmake .. -DLLAMA_CURL=ON && \
    cmake --build . --config Release --target llama-server

# Копируем модель Qwen3
COPY Qwen3-8b-ru.i1-Q6_K.gguf /models/

# Запуск сервера
CMD ["./build/bin/llama-server", "-m", "/models/Qwen3-8b-ru.i1-Q6_K.gguf", "-c", "2048", "-ngl", "1", "-t", "4", "--port", "8001", "--host", "0.0.0.0"]