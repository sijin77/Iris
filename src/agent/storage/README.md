# Архитектура Хранилищ

## Обзор

Система использует абстрактные интерфейсы для всех типов хранилищ, что позволяет легко заменить конкретные реализации БД без изменения основного кода.

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Абстрактные Интерфейсы                   │
├─────────────────────────────────────────────────────────────┤
│  RelationalStorage  │  VectorStorage  │  ChatMemoryStorage  │
└─────────────────────┴─────────────────┴─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Конкретные Реализации                    │
├─────────────────────────────────────────────────────────────┤
│  SQLiteStorageFactory  │  ChromaStorageFactory  │  ...      │
└────────────────────────┴────────────────────────┴───────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Универсальная Фабрика                       │
│              UniversalStorageFactory                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 StorageManager (Singleton)                  │
└─────────────────────────────────────────────────────────────┘
```

## Текущие Реализации

### Реляционные БД
- ✅ **SQLite** - `SQLiteStorageFactory`
- 🔄 **PostgreSQL** - заготовка (TODO)
- 🔄 **MySQL** - заготовка (TODO)

### Векторные БД
- ✅ **ChromaDB** - `ChromaStorageFactory`
- 🔄 **Weaviate** - заготовка (TODO)
- 🔄 **Pinecone** - заготовка (TODO)
- 🔄 **Qdrant** - заготовка (TODO)

### Память
- ✅ **SQLite** - `SQLiteStorageFactory`
- 🔄 **Redis** - заготовка (TODO)
- 🔄 **PostgreSQL** - заготовка (TODO)

## Замена БД

### 1. Замена SQLite на PostgreSQL

#### Шаг 1: Раскомментировать PostgreSQL в docker-compose.yml
```yaml
postgres:
  image: postgres:15
  environment:
    POSTGRES_DB: iriska
    POSTGRES_USER: iriska
    POSTGRES_PASSWORD: iriska123
  volumes:
    - postgres_data:/var/lib/postgresql/data
  ports:
    - "5432:5432"
  networks:
    - iriska-network
```

#### Шаг 2: Изменить переменные окружения
```yaml
environment:
  DB_TYPE: "postgresql"
  MEMORY_DB_URL: "postgresql://iriska:iriska123@postgres:5432/iriska"
  MEMORY_TYPE: "postgresql"
```

#### Шаг 3: Создать PostgreSQL фабрику
```python
# src/agent/storage/postgresql_storage.py
class PostgreSQLStorageFactory:
    @staticmethod
    def create_relational_storage(config: StorageConfig) -> RelationalStorage:
        return PostgreSQLRelationalStorage(config)
```

### 2. Замена ChromaDB на Weaviate

#### Шаг 1: Раскомментировать Weaviate в docker-compose.yml
```yaml
weaviate:
  image: semitechnologies/weaviate:1.22.4
  ports:
    - "8080:8080"
  environment:
    AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
    DEFAULT_VECTORIZER_MODULE: 'none'
  networks:
    - iriska-network
```

#### Шаг 2: Изменить переменные окружения
```yaml
environment:
  VECTOR_TYPE: "weaviate"
  VECTOR_URL: "http://weaviate:8080"
```

#### Шаг 3: Создать Weaviate фабрику
```python
# src/agent/storage/weaviate_storage.py
class WeaviateStorageFactory:
    @staticmethod
    def create_vector_storage(config: StorageConfig) -> VectorStorage:
        return WeaviateVectorStorage(config)
```

### 3. Замена на Redis для памяти

#### Шаг 1: Раскомментировать Redis в docker-compose.yml
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  networks:
    - iriska-network
```

#### Шаг 2: Изменить переменные окружения
```yaml
environment:
  MEMORY_TYPE: "redis"
  REDIS_URL: "redis://redis:6379"
```

#### Шаг 3: Создать Redis фабрику
```python
# src/agent/storage/redis_storage.py
class RedisStorageFactory:
    @staticmethod
    def create_chat_memory_storage(config: StorageConfig) -> ChatMemoryStorage:
        return RedisChatMemoryStorage(config)
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | Примеры |
|------------|----------|---------|
| `DB_TYPE` | Тип реляционной БД | `sqlite`, `postgresql`, `mysql` |
| `VECTOR_TYPE` | Тип векторной БД | `chroma`, `weaviate`, `pinecone` |
| `MEMORY_TYPE` | Тип памяти | `sqlite`, `redis`, `postgresql` |
| `EMBEDDING_TYPE` | Тип эмбеддингов | `openai`, `sentence-transformers` |

### Примеры конфигураций

#### SQLite + ChromaDB (по умолчанию)
```yaml
environment:
  DB_TYPE: "sqlite"
  VECTOR_TYPE: "chroma"
  MEMORY_TYPE: "sqlite"
```

#### PostgreSQL + Weaviate
```yaml
environment:
  DB_TYPE: "postgresql"
  VECTOR_TYPE: "weaviate"
  MEMORY_TYPE: "postgresql"
```

#### MySQL + Pinecone
```yaml
environment:
  DB_TYPE: "mysql"
  VECTOR_TYPE: "pinecone"
  MEMORY_TYPE: "redis"
```

## Добавление новой БД

### 1. Создать реализацию
```python
# src/agent/storage/new_db_storage.py
class NewDBRelationalStorage(RelationalStorage):
    def __init__(self, config: StorageConfig):
        # Реализация
        pass

class NewDBStorageFactory:
    @staticmethod
    def create_relational_storage(config: StorageConfig) -> RelationalStorage:
        return NewDBRelationalStorage(config)
```

### 2. Зарегистрировать в фабрике
```python
# src/agent/storage/factory.py
elif self.config.db_type == "newdb":
    factories["relational"] = NewDBStorageFactory
```

### 3. Добавить в docker-compose.yml
```yaml
newdb:
  image: newdb:latest
  # конфигурация
```

## Преимущества архитектуры

1. **Гибкость** - легко заменить любую БД
2. **Тестируемость** - можно использовать моки
3. **Расширяемость** - просто добавить новую БД
4. **Совместимость** - старый код продолжает работать
5. **Конфигурируемость** - настройка через переменные окружения

## Миграция данных

При замене БД может потребоваться миграция данных:

```python
# src/agent/storage/migrations/
class DataMigrator:
    def migrate_sqlite_to_postgresql(self):
        # Логика миграции
        pass
    
    def migrate_chroma_to_weaviate(self):
        # Логика миграции
        pass
```

## Тестирование

```python
# tests/test_storage.py
def test_storage_switching():
    # Тест переключения между разными БД
    config1 = StorageConfig(db_type="sqlite")
    config2 = StorageConfig(db_type="postgresql")
    
    factory = UniversalStorageFactory(config1)
    storage1 = factory.create_relational_storage()
    
    factory = UniversalStorageFactory(config2)
    storage2 = factory.create_relational_storage()
    
    # Проверяем, что интерфейсы одинаковые
    assert hasattr(storage1, 'init_db')
    assert hasattr(storage2, 'init_db')
```
