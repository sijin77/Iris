"""
Семантический чанкер для разбивки диалогов на логические части.
Решает проблему огромных summaries в ChromaDB.
Использует конфигурацию из профиля агента.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Разбивает диалоги на семантически связанные чанки.
    Использует конфигурацию из профиля агента для персонализации.
    
    Стратегии чанкинга:
    1. По темам разговора (topic-based)
    2. По временным промежуткам (time-based)  
    3. По смене контекста (context-shift)
    4. По важности сообщений (importance-based)
    5. Гибридный подход (hybrid)
    """
    
    def __init__(self, 
                 config: Optional[Dict[str, Any]] = None,
                 max_chunk_size: int = 512,
                 overlap_size: int = 50,
                 min_chunk_size: int = 100):
        """
        Инициализация чанкера с конфигурацией
        
        Args:
            config: Конфигурация из профиля агента (приоритет)
            max_chunk_size: Максимальный размер чанка (fallback)
            overlap_size: Размер перекрытия (fallback)
            min_chunk_size: Минимальный размер чанка (fallback)
        """
        # Используем конфигурацию если предоставлена, иначе параметры по умолчанию
        if config:
            self.max_chunk_size = config.get("max_chunk_size", max_chunk_size)
            self.overlap_size = config.get("overlap_size", overlap_size)
            self.min_chunk_size = config.get("min_chunk_size", min_chunk_size)
            
            # Пороги
            self.high_importance_threshold = config.get("thresholds", {}).get("high_importance", 0.8)
            self.medium_importance_threshold = config.get("thresholds", {}).get("medium_importance", 0.5)
            self.time_gap_threshold = config.get("thresholds", {}).get("time_gap", 300)
            
            # Веса
            self.importance_weights = config.get("weights", {}).get("importance", {})
            
            # Паттерны из конфигурации
            patterns = config.get("patterns", {})
            self.topic_shift_patterns = patterns.get("topic_shift", self._get_default_topic_patterns())
            self.question_patterns = patterns.get("questions", self._get_default_question_patterns())
            self.completion_patterns = patterns.get("completion", self._get_default_completion_patterns())
            self.temporal_absolute_markers = patterns.get("temporal_absolute", self._get_default_temporal_absolute())
            self.temporal_relative_markers = patterns.get("temporal_relative", self._get_default_temporal_relative())
            self.high_importance_keywords = patterns.get("importance_high", self._get_default_high_importance())
            self.medium_importance_keywords = patterns.get("importance_medium", self._get_default_medium_importance())
            self.context_shift_markers = patterns.get("context_shift", self._get_default_context_shift())
            self.technical_context_markers = patterns.get("technical_context", self._get_default_technical_context())
            self.emotional_context_markers = patterns.get("emotional_context", self._get_default_emotional_context())
            
        else:
            # Fallback на значения по умолчанию
            self.max_chunk_size = max_chunk_size
            self.overlap_size = overlap_size
            self.min_chunk_size = min_chunk_size
            
            self.high_importance_threshold = 0.8
            self.medium_importance_threshold = 0.5
            self.time_gap_threshold = 300
            
            self.importance_weights = self._get_default_importance_weights()
            
            # Паттерны по умолчанию
            self.topic_shift_patterns = self._get_default_topic_patterns()
            self.question_patterns = self._get_default_question_patterns()
            self.completion_patterns = self._get_default_completion_patterns()
            self.temporal_absolute_markers = self._get_default_temporal_absolute()
            self.temporal_relative_markers = self._get_default_temporal_relative()
            self.high_importance_keywords = self._get_default_high_importance()
            self.medium_importance_keywords = self._get_default_medium_importance()
            self.context_shift_markers = self._get_default_context_shift()
            self.technical_context_markers = self._get_default_technical_context()
            self.emotional_context_markers = self._get_default_emotional_context()
        
        # Объединяем все временные маркеры для удобства
        self.time_markers = self.temporal_absolute_markers + self.temporal_relative_markers
        
        logger.info(f"SemanticChunker initialized: max_size={self.max_chunk_size}, overlap={self.overlap_size}, config_provided={config is not None}")
    
    def _get_default_topic_patterns(self) -> List[str]:
        """Паттерны смены темы по умолчанию"""
        return [
            r"кстати|by the way|а еще|теперь о|давай поговорим",
            r"другой вопрос|другая тема|переходим к",
            r"забыл спросить|еще хотел|кстати да",
            r"а что насчет|а как же|а про",
            r"меняя тему|changing topic|new topic"
        ]
    
    def _get_default_question_patterns(self) -> List[str]:
        """Паттерны вопросов по умолчанию"""
        return [
            r"как\s+(?:дела|настроение|ты|вы)",
            r"что\s+(?:думаешь|скажешь|посоветуешь)",
            r"можешь\s+(?:помочь|рассказать|объяснить)",
            r"расскажи\s+(?:про|о|мне)"
        ]
    
    def _get_default_completion_patterns(self) -> List[str]:
        """Паттерны завершения темы по умолчанию"""
        return [
            r"понятно|ясно|спасибо|thanks|got it",
            r"все ясно|все понял|все поняла",
            r"отлично|хорошо|супер|perfect|great"
        ]
    
    def _get_default_temporal_absolute(self) -> List[str]:
        """Абсолютные временные маркеры по умолчанию"""
        return [
            r"вчера|сегодня|завтра|послезавтра",
            r"yesterday|today|tomorrow",
            r"на прошлой неделе|на этой неделе|на следующей неделе"
        ]
    
    def _get_default_temporal_relative(self) -> List[str]:
        """Относительные временные маркеры по умолчанию"""
        return [
            r"утром|днем|вечером|ночью",
            r"morning|afternoon|evening|night",
            r"недавно|давно|скоро|потом"
        ]
    
    def _get_default_high_importance(self) -> List[str]:
        """Ключевые слова высокой важности по умолчанию"""
        return [
            "важно", "срочно", "критично", "проблема", "ошибка",
            "не работает", "сломалось", "помогите", "help",
            "urgent", "important", "critical", "error", "broken",
            "решение", "вывод", "итог", "conclusion", "result"
        ]
    
    def _get_default_medium_importance(self) -> List[str]:
        """Ключевые слова средней важности по умолчанию"""
        return [
            "вопрос", "как", "почему", "что", "когда", "где",
            "можно", "нужно", "хочу", "планирую", "думаю",
            "question", "how", "why", "what", "when", "where",
            "can", "should", "want", "plan", "think"
        ]
    
    def _get_default_context_shift(self) -> List[str]:
        """Маркеры смены контекста по умолчанию"""
        return [
            r"но\s+(?:сейчас|теперь|давайте)",
            r"однако|however|but now",
            r"с другой стороны|on the other hand",
            r"возвращаясь к|getting back to|back to"
        ]
    
    def _get_default_technical_context(self) -> List[str]:
        """Маркеры технического контекста по умолчанию"""
        return [
            r"код|code|программа|program|скрипт|script",
            r"ошибка|error|баг|bug|исключение|exception",
            r"база данных|database|SQL|запрос|query",
            r"API|REST|HTTP|JSON|XML"
        ]
    
    def _get_default_emotional_context(self) -> List[str]:
        """Маркеры эмоционального контекста по умолчанию"""
        return [
            r"нравится|не нравится|like|dislike",
            r"хорошо|плохо|good|bad|отлично|excellent",
            r"расстроен|радуюсь|грустно|весело",
            r"спасибо|thanks|благодарю|appreciate"
        ]
    
    def _get_default_importance_weights(self) -> Dict[str, float]:
        """Веса важности по умолчанию"""
        return {
            "high_keywords": 0.3,
            "medium_keywords": 0.15,
            "message_length": 0.1,
            "question_marks": 0.1,
            "exclamation_marks": 0.05,
            "caps_ratio": 0.05,
            "user_feedback": 0.25
        }
    
    def chunk_dialogue(self, messages: List[Dict[str, Any]], 
                      strategy: str = "hybrid") -> List[Dict[str, Any]]:
        """
        Разбивает диалог на семантические чанки
        
        Args:
            messages: Список сообщений диалога
            strategy: Стратегия чанкинга (topic, time, context, importance, hybrid)
            
        Returns:
            Список чанков с метаданными
        """
        if not messages:
            return []
        
        try:
            if strategy == "topic":
                return self._chunk_by_topics(messages)
            elif strategy == "time":
                return self._chunk_by_time(messages)
            elif strategy == "context":
                return self._chunk_by_context_shift(messages)
            elif strategy == "importance":
                return self._chunk_by_importance(messages)
            else:  # hybrid
                return self._chunk_hybrid(messages)
                
        except Exception as e:
            logger.error(f"Error chunking dialogue: {e}")
            # Fallback: простое разбиение по размеру
            return self._chunk_by_size(messages)
    
    def _chunk_by_topics(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Чанкинг по темам разговора"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, message in enumerate(messages):
            message_text = message.get("content", "")
            message_size = len(message_text)
            
            # Проверяем смену темы
            topic_shift = self._detect_topic_shift(message_text, i > 0)
            
            # Если смена темы и текущий чанк не пустой
            if topic_shift and current_chunk and current_size > self.min_chunk_size:
                chunk = self._create_chunk(current_chunk, "topic_boundary")
                chunks.append(chunk)
                
                # Добавляем перекрытие
                overlap_msgs = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_msgs.copy()
                current_size = sum(len(msg.get("content", "")) for msg in current_chunk)
            
            current_chunk.append(message)
            current_size += message_size
            
            # Проверяем размер чанка
            if current_size >= self.max_chunk_size:
                chunk = self._create_chunk(current_chunk, "size_limit")
                chunks.append(chunk)
                
                # Перекрытие
                overlap_msgs = current_chunk[-2:] if len(current_chunk) >= 2 else []
                current_chunk = overlap_msgs
                current_size = sum(len(msg.get("content", "")) for msg in current_chunk)
        
        # Добавляем последний чанк
        if current_chunk:
            chunk = self._create_chunk(current_chunk, "end_of_dialogue")
            chunks.append(chunk)
        
        logger.info(f"Topic chunking: {len(messages)} messages → {len(chunks)} chunks")
        return chunks
    
    def _chunk_by_time(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Чанкинг по временным промежуткам"""
        chunks = []
        current_chunk = []
        current_size = 0
        last_timestamp = None
        time_gap_threshold = 300  # 5 минут
        
        for message in messages:
            message_text = message.get("content", "")
            message_size = len(message_text)
            timestamp = message.get("timestamp")
            
            # Проверяем временной разрыв
            if (last_timestamp and timestamp and 
                abs(timestamp - last_timestamp) > time_gap_threshold and
                current_size > self.min_chunk_size):
                
                chunk = self._create_chunk(current_chunk, "time_gap")
                chunks.append(chunk)
                current_chunk = []
                current_size = 0
            
            current_chunk.append(message)
            current_size += message_size
            last_timestamp = timestamp
            
            # Проверяем размер
            if current_size >= self.max_chunk_size:
                chunk = self._create_chunk(current_chunk, "size_limit")
                chunks.append(chunk)
                
                overlap_msgs = current_chunk[-1:] if current_chunk else []
                current_chunk = overlap_msgs
                current_size = sum(len(msg.get("content", "")) for msg in current_chunk)
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, "end_of_dialogue")
            chunks.append(chunk)
        
        logger.info(f"Time chunking: {len(messages)} messages → {len(chunks)} chunks")
        return chunks
    
    def _chunk_by_context_shift(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Чанкинг по смене контекста"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, message in enumerate(messages):
            message_text = message.get("content", "")
            message_size = len(message_text)
            
            # Определяем смену контекста
            context_shift = self._detect_context_shift(message, messages, i)
            
            if context_shift and current_chunk and current_size > self.min_chunk_size:
                chunk = self._create_chunk(current_chunk, "context_shift")
                chunks.append(chunk)
                
                # Сохраняем контекст
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_size = len(current_chunk[0].get("content", "")) if current_chunk else 0
            
            current_chunk.append(message)
            current_size += message_size
            
            if current_size >= self.max_chunk_size:
                chunk = self._create_chunk(current_chunk, "size_limit")
                chunks.append(chunk)
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, "end_of_dialogue")
            chunks.append(chunk)
        
        logger.info(f"Context chunking: {len(messages)} messages → {len(chunks)} chunks")
        return chunks
    
    def _chunk_by_importance(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Чанкинг по важности сообщений"""
        # Сначала оцениваем важность каждого сообщения
        for message in messages:
            importance = self._calculate_message_importance(message)
            message["importance"] = importance
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for message in messages:
            message_text = message.get("content", "")
            message_size = len(message_text)
            importance = message.get("importance", 0.5)
            
            # Если сообщение очень важное, начинаем новый чанк
            if (importance > 0.8 and current_chunk and 
                current_size > self.min_chunk_size):
                
                chunk = self._create_chunk(current_chunk, "high_importance")
                chunks.append(chunk)
                current_chunk = []
                current_size = 0
            
            current_chunk.append(message)
            current_size += message_size
            
            if current_size >= self.max_chunk_size:
                chunk = self._create_chunk(current_chunk, "size_limit")
                chunks.append(chunk)
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, "end_of_dialogue")
            chunks.append(chunk)
        
        logger.info(f"Importance chunking: {len(messages)} messages → {len(chunks)} chunks")
        return chunks
    
    def _chunk_hybrid(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Гибридная стратегия чанкинга"""
        # Комбинируем несколько подходов
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, message in enumerate(messages):
            message_text = message.get("content", "")
            message_size = len(message_text)
            
            # Вычисляем факторы для разбиения
            topic_shift = self._detect_topic_shift(message_text, i > 0)
            context_shift = self._detect_context_shift(message, messages, i)
            importance = self._calculate_message_importance(message)
            
            # Решение о разбиении на основе нескольких факторов
            should_split = (
                (topic_shift and current_size > self.min_chunk_size) or
                (context_shift and current_size > self.min_chunk_size * 0.7) or
                (importance > 0.9 and current_size > self.min_chunk_size * 0.5) or
                (current_size >= self.max_chunk_size)
            )
            
            if should_split and current_chunk:
                split_reason = self._determine_split_reason(topic_shift, context_shift, importance, current_size)
                chunk = self._create_chunk(current_chunk, split_reason)
                chunks.append(chunk)
                
                # Умное перекрытие на основе важности
                overlap_size = min(2, len(current_chunk))
                if importance > 0.7:
                    overlap_size = min(3, len(current_chunk))
                
                current_chunk = current_chunk[-overlap_size:] if overlap_size > 0 else []
                current_size = sum(len(msg.get("content", "")) for msg in current_chunk)
            
            current_chunk.append(message)
            current_size += message_size
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, "end_of_dialogue")
            chunks.append(chunk)
        
        logger.info(f"Hybrid chunking: {len(messages)} messages → {len(chunks)} chunks")
        return chunks
    
    def _chunk_by_size(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Простое разбиение по размеру (fallback)"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for message in messages:
            message_size = len(message.get("content", ""))
            
            if current_size + message_size > self.max_chunk_size and current_chunk:
                chunk = self._create_chunk(current_chunk, "size_limit")
                chunks.append(chunk)
                current_chunk = []
                current_size = 0
            
            current_chunk.append(message)
            current_size += message_size
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, "end_of_dialogue")
            chunks.append(chunk)
        
        return chunks
    
    def _detect_topic_shift(self, message_text: str, has_previous: bool) -> bool:
        """Определяет смену темы в сообщении"""
        if not has_previous:
            return False
        
        message_lower = message_text.lower()
        
        for pattern in self.topic_shift_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _detect_context_shift(self, message: Dict[str, Any], 
                            all_messages: List[Dict[str, Any]], 
                            current_index: int) -> bool:
        """Определяет смену контекста"""
        if current_index == 0:
            return False
        
        current_text = message.get("content", "").lower()
        
        # Проверяем временные маркеры
        for pattern in self.time_markers:
            if re.search(pattern, current_text):
                return True
        
        # Проверяем смену ролей в диалоге
        current_role = message.get("role", "")
        prev_role = all_messages[current_index - 1].get("role", "")
        
        if current_role != prev_role and current_role == "user":
            # Пользователь начал новую тему
            return True
        
        return False
    
    def _calculate_message_importance(self, message: Dict[str, Any]) -> float:
        """Рассчитывает важность сообщения используя конфигурируемые веса и ключевые слова"""
        content = message.get("content", "")
        importance = 0.5  # базовая важность
        
        content_lower = content.lower()
        
        # Проверяем ключевые слова высокой важности
        high_keyword_count = sum(1 for word in self.high_importance_keywords if word.lower() in content_lower)
        if high_keyword_count > 0:
            importance += high_keyword_count * self.importance_weights.get("high_keywords", 0.3)
        
        # Проверяем ключевые слова средней важности
        medium_keyword_count = sum(1 for word in self.medium_importance_keywords if word.lower() in content_lower)
        if medium_keyword_count > 0:
            importance += medium_keyword_count * self.importance_weights.get("medium_keywords", 0.15)
        
        # Длина сообщения
        if len(content) > 200:
            importance += self.importance_weights.get("message_length", 0.1)
        
        # Наличие вопросительных знаков
        question_mark_count = content.count("?") + content.count("?")
        if question_mark_count > 0:
            importance += question_mark_count * self.importance_weights.get("question_marks", 0.1)
        
        # Наличие восклицательных знаков
        exclamation_count = content.count("!") + content.count("!")
        if exclamation_count > 0:
            importance += exclamation_count * self.importance_weights.get("exclamation_marks", 0.05)
        
        # Соотношение заглавных букв
        if len(content) > 0:
            caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if caps_ratio > 0.3:  # Если более 30% заглавных букв
                importance += caps_ratio * self.importance_weights.get("caps_ratio", 0.05)
        
        # Обратная связь пользователя (если есть в метаданных)
        if message.get("is_feedback", False):
            importance += self.importance_weights.get("user_feedback", 0.25)
        
        return min(1.0, importance)
    
    def _determine_split_reason(self, topic_shift: bool, context_shift: bool, 
                               importance: float, current_size: int) -> str:
        """Определяет причину разбиения чанка"""
        if current_size >= self.max_chunk_size:
            return "size_limit"
        elif topic_shift:
            return "topic_shift"
        elif context_shift:
            return "context_shift"
        elif importance > 0.9:
            return "high_importance"
        else:
            return "hybrid_decision"
    
    def _create_chunk(self, messages: List[Dict[str, Any]], split_reason: str) -> Dict[str, Any]:
        """Создает чанк с метаданными"""
        if not messages:
            return {}
        
        # Объединяем содержимое сообщений
        content_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role and content:
                content_parts.append(f"{role}: {content}")
            elif content:
                content_parts.append(content)
        
        chunk_content = "\n".join(content_parts)
        
        # Рассчитываем метаданные
        timestamps = [msg.get("timestamp") for msg in messages if msg.get("timestamp")]
        importances = [self._calculate_message_importance(msg) for msg in messages]
        
        chunk = {
            "content": chunk_content,
            "message_count": len(messages),
            "chunk_size": len(chunk_content),
            "split_reason": split_reason,
            "start_timestamp": min(timestamps) if timestamps else None,
            "end_timestamp": max(timestamps) if timestamps else None,
            "avg_importance": sum(importances) / len(importances) if importances else 0.5,
            "max_importance": max(importances) if importances else 0.5,
            "created_at": datetime.now().timestamp()
        }
        
        return chunk


# Интеграция с существующей системой
class ChunkedMemoryStorage:
    """Адаптер для работы с чанкованной памятью"""
    
    def __init__(self, chunker: SemanticChunker, vector_storage):
        self.chunker = chunker
        self.vector_storage = vector_storage
        
    async def save_dialogue_chunks(self, user_id: str, messages: List[Dict[str, Any]], 
                                  strategy: str = "hybrid") -> int:
        """Сохраняет диалог в виде чанков"""
        try:
            chunks = self.chunker.chunk_dialogue(messages, strategy)
            
            saved_count = 0
            for i, chunk in enumerate(chunks):
                # Добавляем метаданные для поиска
                chunk["user_id"] = user_id
                chunk["chunk_index"] = i
                chunk["total_chunks"] = len(chunks)
                
                # Сохраняем в векторную БД
                if await self._save_chunk_to_vector_db(chunk):
                    saved_count += 1
            
            logger.info(f"Saved {saved_count}/{len(chunks)} chunks for user {user_id}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving dialogue chunks: {e}")
            return 0
    
    async def _save_chunk_to_vector_db(self, chunk: Dict[str, Any]) -> bool:
        """Сохраняет чанк в векторную БД"""
        try:
            # Здесь интеграция с ChromaDB или другой векторной БД
            # Пример для ChromaDB через LangChain
            if hasattr(self.vector_storage, 'add_texts'):
                self.vector_storage.add_texts(
                    [chunk["content"]], 
                    metadatas=[{k: v for k, v in chunk.items() if k != "content"}]
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving chunk to vector DB: {e}")
            return False
