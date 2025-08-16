import requests
import logging
logger = logging.getLogger(__name__)

try:
    resp = requests.post(
        "http://localhost:8001/completion",
        json={"prompt": "Hello, how are you?", "n_predict": 64}
    )
    print(resp.json())
except Exception as e:
    logger.exception(f"Ошибка при запросе к LLM серверу: {e}")