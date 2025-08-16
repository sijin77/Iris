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
