import os
import httpx
import logging

logger = logging.getLogger(__name__)

LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://localhost:8001")

# TODO (llm_client):
# - Реализовать streaming (POST /completion с stream=True, чтение чанков)
# - Ретраи, бэкофф, отдельные таймауты на connect/read
# - Конфигурируемые параметры: n_predict, top_k, top_p, stop, температура
# - Единый интерфейс ошибок и коды возврата для верхних уровней
# - Логи с метриками: длительность запроса, размеры промпта/ответа
# - Поддержка мультимодальности (если модель поддерживает) и structured outputs

async def llama_cpp_completion(prompt: str) -> str:
    url = f"{LLM_SERVER_URL}/completion"
    payload = {
        "prompt": prompt,
        "n_predict": 256,
        "temperature": 0.7,
        "stop": ["</s>", "\nUser:"]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("content") or data.get("completion") or "[Нет ответа от LLM]"
    except httpx.RequestError as e:
        logger.error(f"Ошибка запроса к LLM серверу: {e}")
        return "[Ошибка связи с LLM сервером]"
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при обращении к LLM: {e}")
        return "[Внутренняя ошибка LLM]" 