"""
Долговременная память (S3 + Vector DB)
Проблема S3:

Нет семантического поиска

Высокая задержка

Решение:

S3 — сырые данные с метаинформацией

ChromaDB/Weaviate — векторные индексы
"""

from sentence_transformers import SentenceTransformer


class EnhancedLongTermMemory(IMemoryStorage):
    def __init__(self, s3, vector_db, encoder_model: str="all-MiniLM-L6-v2"):
        self.s3 = s3
        self.vector_db = vector_db
        self.encoder = SentenceTransformer(encoder_model)
        self.encoder.max_seq_length = 512  # Оптимизация памяти
        
    async def save(self, fragment: MemoryFragment) -> str:
        # Асинхронная обработка
        loop = asyncio.get_event_loop()
        
        # 1. Сохранение в S3 с оптимизацией
        s3_key = f"memory/v2/{fragment.timestamp}_{fragment.id}.json"
        await self.s3.put(
            Body=fragment.json(),
            Key=s3_key,
            Metadata={
                'priority': str(fragment.priority),
                'source': 'working_memory'
            }
        )
        
        # 2. Векторизация в отдельном потоке
        vector = await loop.run_in_executor(
            None, 
            lambda: self.encoder.encode(fragment.text[:2000])  # Обрезка для стабильности
            
        # 3. Сохранение вектора
        await self.vector_db.upsert(
            vectors=[{
                'id': fragment.id,
                'vector': vector,
                'metadata': {
                    's3_key': s3_key,
                    'timestamp': fragment.timestamp,
                    'priority': fragment.priority,
                    'text_hash': hashlib.md5(fragment.text.encode()).hexdigest()
                }
            }],
            namespace='memory'
        )
        
        return s3_key

    async def search(self, query: str, limit: int=5) -> List[MemoryFragment]:
        # Векторизация запроса
        query_vector = self.encoder.encode(query)
        
        # Поиск в векторной БД
        results = await self.vector_db.query(
            vector=query_vector,
            top_k=limit,
            include_metadata=True
        )
        
        # Загрузка полных данных из S3
        fragments = []
        for match in results.matches:
            s3_key = match.metadata['s3_key']
            data = await self.s3.get(Key=s3_key)
            fragments.append(MemoryFragment.parse_raw(data))
            
        return fragments