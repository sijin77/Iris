# Работа с PostgreSQL/S3
import psycopg2
from pgvector.psycopg2 import register_vector


# Нейромодуляция (дофаминовые метки)
def apply_dopamine(fragment, reward):
    """Аналог дофаминового подкрепления"""
    fragment.priority *= 1 + reward
    fragment.metadata["neuro_modulator"] = "dopamine"
    return fragment


# Механизм забвения, нужен ли?
class ForgettingMechanism:
    def __init__(self, redis, s3):
        self.redis = redis
        self.s3 = s3

    async def run(self):
        # 1. Анализ приоритетов в рабочей памяти
        memories = await self.redis.zrange("working_memory", 0, -1, withscores=True)

        # 2. Удаление низкоприоритетных
        for mem_id, score in memories:
            if score < self._threshold():
                await self._forget(mem_id)

    async def _forget(self, mem_id):
        """Контролируемое забывание"""
        await self.redis.delete(f"memory:{mem_id}")
        await self.redis.zrem("working_memory", mem_id)
        # В S3 остается как "архив"


# Набросок сохранения диалога
class MemoryManager:
    def __init__(self, db_url: str):
        self.conn = psycopg2.connect(db_url)
        register_vector(self.conn)

    def save_dialogue(self, text: str, embedding: list[float]):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dialogues (text, vector) VALUES (%s, %s)",
                (text, embedding),
            )
        self.conn.commit()

    def search_memories(self, query: str, limit=5) -> list[str]:
        # Поиск по вектору или тексту
        ...
