"""
Модуль памяти как кэш-системы для агента Iriska.

Предоставляет автоматическое управление данными между уровнями памяти:
- L1: Redis (горячий кэш)
- L2: SQLite (теплое хранилище)  
- L3: ChromaDB (векторное хранилище)
- L4: S3/DB (холодный архив)
"""

from .models import (
    MemoryFragment,
    MemoryLevel,
    FragmentType,
    MemoryConfig,
    MemoryStats,
    AccessPattern,
    ActivityScore
)

from .interfaces import (
    IMemoryComponent,
    IDataPromoter,
    IDataDemoter,
    IDataEvictor,
    IMemoryAnalyzer,
    IMemoryOptimizer,
    IMemoryMonitor,
    IMemoryStorage
)

from .controller import MemoryController
from .controller_integration import EnhancedMemoryController
from .promoter import DataPromoter
from .demoter import DataDemoter
from .evictor import DataEvictor
from .multi_level_storage import MultiLevelMemoryStorage
from .langchain_adapter import (
    LangChainMemoryAdapter,
    MemoryControllerChatHistory,
    create_memory_controller_for_langchain,
    integrate_with_existing_langchain_app
)

__all__ = [
    # Модели
    "MemoryFragment",
    "MemoryLevel", 
    "FragmentType",
    "MemoryConfig",
    "MemoryStats",
    "AccessPattern",
    "ActivityScore",
    
    # Интерфейсы
    "IMemoryComponent",
    "IDataPromoter",
    "IDataDemoter", 
    "IDataEvictor",
    "IMemoryAnalyzer",
    "IMemoryOptimizer",
    "IMemoryMonitor",
    "IMemoryStorage",
    
    # Реализации
    "MemoryController",
    "EnhancedMemoryController",
    "MultiLevelMemoryStorage",
    "DataPromoter",
    "DataDemoter",
    "DataEvictor",
    
    # LangChain интеграция
    "LangChainMemoryAdapter",
    "MemoryControllerChatHistory", 
    "create_memory_controller_for_langchain",
    "integrate_with_existing_langchain_app",
]

# Storage компоненты (опциональные импорты)
try:
    from ..storage.redis_storage import RedisMemoryStorage
    __all__.append('RedisMemoryStorage')
except ImportError:
    pass

try:
    from ..storage.chroma_storage import ChromaVectorStorage  
    __all__.append('ChromaVectorStorage')
except ImportError:
    pass

try:
    from ..storage.sqlite_storage import SQLiteStorage
    __all__.append('SQLiteStorage')
except ImportError:
    pass

try:
    from ..storage.mock_cold_storage import MockColdStorage
    __all__.append('MockColdStorage')
except ImportError:
    pass

__version__ = "0.1.0"
__author__ = "Iriska Team"
__description__ = "Memory management system as cache hierarchy for Iriska AI agent"
