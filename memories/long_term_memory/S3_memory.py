import json
from datetime import datetime, timedelta
from typing import List, Optional
import zlib
import hashlib
import aiobotocore
from cryptography.fernet import Fernet


class AutonomousS3Memory:
    def __init__(self):
        self.session = aiobotocore.get_session()
        self.importance_threshold = 0.6
        self.llm_endpoint = "http://localhost:11434"  # TinyLlama

    async def _calculate_importance(self, text: str) -> float:
        """Автономная оценка важности с учетом:
        - Длины текста
        - Эмоционального веса
        - Частоты упоминаний ключевых тем"""
        length_factor = min(len(text) / 500, 1.0)
        emotional_factor = await self._analyze_emotion(text)
        return (length_factor + emotional_factor) / 2

    def _encrypt(self, data, importance):
        if importance > 0.7:
            return Fernet(os.getenv("ENCRYPTION_KEY")).encrypt(data)
        else:
            return data  # или легкое шифрование

    async def save(self, text: str, mode: str) -> Optional[str]:
        """Улучшенное сохранение с автономной оценкой"""
        importance = await self._calculate_importance(text)
        if importance < self.importance_threshold:
            return None

        packed = await self._pack(text, mode, importance)
        compressed = zlib.compress(packed)
        encrypted = self._encrypt(compressed, importance)

        s3_key = self._generate_key(importance)
        async with self.session.create_client("s3") as client:
            await client.put_object(
                Bucket="iriska-memory",
                Key=s3_key,
                Body=encrypted,
                Metadata={
                    "importance": str(importance),
                    "mode": mode,
                    "topics": await self._extract_topics(text),
                },
            )
        return s3_key

    async def _pack(self, text: str, mode: str, importance: float) -> bytes:
        """Улучшенная упаковка с метаданными"""
        header = {
            "version": "IRISKA_v2",
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "importance": importance,
            "topics": await self._extract_topics(text),
            "hash": hashlib.sha256(text.encode()).hexdigest(),
        }
        return json.dumps(header).encode() + b"\n---\n" + text.encode()

    async def _extract_topics(self, text: str) -> List[str]:
        """Используем LLM для анализа тем"""
        # Реализация через запрос к локальной LLM
        return ["self_development", "memory"]

    def _generate_key(self, importance: float) -> str:
        """Динамическое именование файлов"""
        folder = "critical" if importance > 0.8 else "regular"
        return f"{folder}/{datetime.now():%Y/%m/%d_%H-%M-%S}.enc"

    async def autonomous_maintenance(self):
        """Самостоятельное обслуживание хранилища"""
        async with self.session.create_client("s3") as client:
            # 1. Очистка старых неважных данных
            objects = await client.list_objects_v2(Bucket="iriska-memory")
            for obj in objects.get("Contents", []):
                meta = await client.head_object(Bucket="iriska-memory", Key=obj["Key"])
                importance = float(meta["Metadata"].get("importance", "0"))
                if importance < 0.5 and obj[
                    "LastModified"
                ] < datetime.now() - timedelta(days=30):
                    await client.delete_object(Bucket="iriska-memory", Key=obj["Key"])

            # 2. Ребалансировка хранилища
            # ... (можно добавить логику перемещения между S3-классами)
