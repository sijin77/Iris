"""
Улучшенный ретривер с ранжированием и пост-обработкой результатов.
Решает проблему нерелевантных частей в больших summaries.
Использует конфигурацию из профиля агента для персонализации.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class EnhancedRetriever:
    """
    Улучшенный ретривер с интеллектуальной пост-обработкой результатов.
    Использует конфигурацию из профиля агента для персонализации.
    
    Возможности:
    1. Семантическое ранжирование результатов
    2. Извлечение релевантных частей из больших документов
    3. Контекстная фильтрация
    4. Временное ранжирование
    """
    
    def __init__(self, 
                 base_retriever, 
                 config: Optional[Dict[str, Any]] = None,
                 max_context_length: int = 2000):
        """
        Инициализация ретривера с конфигурацией
        
        Args:
            base_retriever: Базовый ретривер для поиска
            config: Конфигурация из профиля агента (приоритет)
            max_context_length: Максимальная длина контекста (fallback)
        """
        self.base_retriever = base_retriever
        
        # Используем конфигурацию если предоставлена
        if config:
            self.max_context_length = config.get("max_context_length", max_context_length)
            self.min_relevance_score = config.get("thresholds", {}).get("min_relevance", 0.2)
            self.max_extraction_length = config.get("max_extraction_length", 800)
            
            # Веса для ранжирования
            self.ranking_weights = config.get("weights", {}).get("ranking", {
                "relevance": 0.7,
                "temporal": 0.2,
                "importance": 0.1
            })
            
            self.temporal_weights = config.get("weights", {}).get("temporal", {
                "very_recent": 1.0,
                "recent": 0.8,
                "medium": 0.6,
                "old": 0.4
            })
            
            # Паттерны из конфигурации
            patterns = config.get("patterns", {})
            self.relevance_patterns = patterns.get("dialogue", self._get_default_dialogue_patterns())
            
        else:
            # Fallback на значения по умолчанию
            self.max_context_length = max_context_length
            self.min_relevance_score = 0.2
            self.max_extraction_length = 800
            
            self.ranking_weights = {
                "relevance": 0.7,
                "temporal": 0.2,
                "importance": 0.1
            }
            
            self.temporal_weights = {
                "very_recent": 1.0,
                "recent": 0.8,
                "medium": 0.6,
                "old": 0.4
            }
            
            self.relevance_patterns = self._get_default_dialogue_patterns()
        
        logger.info(f"EnhancedRetriever initialized: max_context_length={self.max_context_length}, config_provided={config is not None}")
    
    def _get_default_dialogue_patterns(self) -> Dict[str, str]:
        """Паттерны для извлечения диалогов по умолчанию"""
        return {
            "question_answer": r"(.*?)(?:пользователь:|user:|вопрос:|question:)(.*?)(?:ответ:|answer:|assistant:|агент:)(.*?)(?=пользователь:|user:|$)",
            "topic_discussion": r"(.*?)(?:говорили о|обсуждали|про|about)(.*?)(?=\.|!|\?|$)",
            "problem_solution": r"(.*?)(?:проблема|ошибка|не работает|problem|error)(.*?)(?:решение|исправить|fix|solution)(.*?)(?=\.|!|\?|$)",
            "instruction": r"(.*?)(?:как|how to|инструкция|instruction)(.*?)(?=\.|!|\?|$)",
            "explanation": r"(.*?)(?:объясни|explain|расскажи|tell me)(.*?)(?=\.|!|\?|$)"
        }
    
    async def get_relevant_context(self, query: str, user_id: str = None, 
                                  k: int = 4) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Получает релевантный контекст с интеллектуальной обработкой
        
        Args:
            query: Поисковый запрос
            user_id: ID пользователя (для фильтрации)
            k: Количество документов для поиска
            
        Returns:
            Tuple[контекст, метаданные документов]
        """
        try:
            # 1. Базовый поиск
            raw_docs = await self._base_search(query, k * 2)  # Берем больше для фильтрации
            
            if not raw_docs:
                return "", []
            
            # 2. Фильтрация по пользователю
            if user_id:
                raw_docs = self._filter_by_user(raw_docs, user_id)
            
            # 3. Ранжирование по релевантности
            ranked_docs = self._rank_by_relevance(raw_docs, query)
            
            # 4. Извлечение релевантных частей
            processed_docs = self._extract_relevant_parts(ranked_docs[:k], query)
            
            # 5. Временное ранжирование
            final_docs = self._apply_temporal_ranking(processed_docs)
            
            # 6. Сборка финального контекста
            context = self._build_final_context(final_docs)
            
            logger.info(f"Enhanced retrieval: {len(raw_docs)} → {len(final_docs)} docs, context length: {len(context)}")
            
            return context, final_docs
            
        except Exception as e:
            logger.error(f"Error in enhanced retrieval: {e}")
            return "", []
    
    async def _base_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Базовый поиск через существующий ретривер"""
        try:
            if hasattr(self.base_retriever, 'get_relevant_documents'):
                docs = self.base_retriever.get_relevant_documents(query)
                
                # Конвертируем в наш формат
                result = []
                for doc in docs[:k]:
                    doc_dict = {
                        "content": doc.page_content if hasattr(doc, 'page_content') else str(doc),
                        "metadata": doc.metadata if hasattr(doc, 'metadata') else {},
                        "score": getattr(doc, 'score', 0.5)
                    }
                    result.append(doc_dict)
                
                return result
            
            return []
            
        except Exception as e:
            logger.error(f"Error in base search: {e}")
            return []
    
    def _filter_by_user(self, docs: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """Фильтрует документы по пользователю"""
        filtered = []
        
        for doc in docs:
            doc_user_id = doc.get("metadata", {}).get("user_id")
            if not doc_user_id or doc_user_id == user_id:
                filtered.append(doc)
        
        logger.debug(f"User filtering: {len(docs)} → {len(filtered)} docs")
        return filtered
    
    def _rank_by_relevance(self, docs: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Ранжирует документы по релевантности к запросу"""
        query_words = set(query.lower().split())
        
        for doc in docs:
            content = doc.get("content", "").lower()
            content_words = set(content.split())
            
            # Простое пересечение слов
            intersection = query_words.intersection(content_words)
            jaccard_similarity = len(intersection) / len(query_words.union(content_words)) if query_words.union(content_words) else 0
            
            # Учитываем позицию вхождений
            position_bonus = 0
            for word in query_words:
                if word in content:
                    # Бонус за раннее вхождение
                    position = content.find(word)
                    position_bonus += max(0, 1 - position / len(content))
            
            position_bonus /= len(query_words) if query_words else 1
            
            # Итоговая оценка релевантности
            doc["relevance_score"] = jaccard_similarity * 0.7 + position_bonus * 0.3
        
        # Сортируем по релевантности
        docs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return docs
    
    def _extract_relevant_parts(self, docs: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Извлекает релевантные части из документов"""
        processed_docs = []
        
        for doc in docs:
            content = doc.get("content", "")
            
            # Пытаемся найти наиболее релевантную часть
            best_part = self._find_best_content_part(content, query)
            
            if best_part:
                processed_doc = doc.copy()
                processed_doc["original_content"] = content
                processed_doc["content"] = best_part
                processed_doc["extraction_method"] = "pattern_based"
                processed_docs.append(processed_doc)
            else:
                # Если не нашли паттерн, берем начало документа
                truncated = self._smart_truncate(content, query)
                processed_doc = doc.copy()
                processed_doc["original_content"] = content
                processed_doc["content"] = truncated
                processed_doc["extraction_method"] = "truncation"
                processed_docs.append(processed_doc)
        
        return processed_docs
    
    def _find_best_content_part(self, content: str, query: str) -> Optional[str]:
        """Находит наиболее релевантную часть контента"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Ищем по паттернам
        for pattern_name, pattern in self.relevance_patterns.items():
            matches = re.finditer(pattern, content_lower, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                matched_text = match.group(0)
                
                # Проверяем, содержит ли найденная часть слова из запроса
                query_words = set(query_lower.split())
                matched_words = set(matched_text.split())
                
                if len(query_words.intersection(matched_words)) >= len(query_words) * 0.3:
                    # Возвращаем соответствующую часть оригинального текста
                    start, end = match.span()
                    return content[start:end].strip()
        
        # Ищем абзацы, содержащие слова из запроса
        paragraphs = content.split('\n\n')
        best_paragraph = None
        best_score = 0
        
        query_words = set(query_lower.split())
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) < 50:  # Слишком короткий абзац
                continue
            
            paragraph_words = set(paragraph.lower().split())
            intersection = query_words.intersection(paragraph_words)
            score = len(intersection) / len(query_words) if query_words else 0
            
            if score > best_score and score > 0.2:
                best_score = score
                best_paragraph = paragraph.strip()
        
        return best_paragraph
    
    def _smart_truncate(self, content: str, query: str, max_length: int = 800) -> str:
        """Умное усечение контента с сохранением релевантных частей"""
        if len(content) <= max_length:
            return content
        
        query_words = set(query.lower().split())
        
        # Ищем позицию первого вхождения слова из запроса
        first_occurrence = len(content)
        for word in query_words:
            pos = content.lower().find(word)
            if pos != -1 and pos < first_occurrence:
                first_occurrence = pos
        
        # Определяем окно вокруг первого вхождения
        window_start = max(0, first_occurrence - max_length // 3)
        window_end = min(len(content), window_start + max_length)
        
        # Корректируем границы по словам
        if window_start > 0:
            # Ищем ближайший пробел
            space_pos = content.find(' ', window_start)
            if space_pos != -1 and space_pos - window_start < 50:
                window_start = space_pos + 1
        
        if window_end < len(content):
            # Ищем ближайший пробел в обратную сторону
            space_pos = content.rfind(' ', window_start, window_end)
            if space_pos != -1 and window_end - space_pos < 50:
                window_end = space_pos
        
        truncated = content[window_start:window_end].strip()
        
        # Добавляем индикаторы усечения
        if window_start > 0:
            truncated = "..." + truncated
        if window_end < len(content):
            truncated = truncated + "..."
        
        return truncated
    
    def _apply_temporal_ranking(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Применяет временное ранжирование"""
        current_time = datetime.now().timestamp()
        
        for doc in docs:
            timestamp = doc.get("metadata", {}).get("timestamp")
            
            if timestamp:
                try:
                    # Конвертируем timestamp в float если нужно
                    if isinstance(timestamp, str):
                        doc_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
                    else:
                        doc_time = float(timestamp)
                    
                    # Рассчитываем временной вес (более свежие документы важнее)
                    age_hours = (current_time - doc_time) / 3600
                    
                    if age_hours < 24:
                        temporal_weight = self.temporal_weights.get("very_recent", 1.0)  # Очень свежие
                    elif age_hours < 168:  # Неделя
                        temporal_weight = self.temporal_weights.get("recent", 0.8)
                    elif age_hours < 720:  # Месяц
                        temporal_weight = self.temporal_weights.get("medium", 0.6)
                    else:
                        temporal_weight = self.temporal_weights.get("old", 0.4)  # Старые
                    
                    doc["temporal_weight"] = temporal_weight
                    
                    # Комбинируем с релевантностью используя конфигурируемые веса
                    relevance = doc.get("relevance_score", 0.5)
                    importance = doc.get("importance_score", 0.5)
                    
                    relevance_weight = self.ranking_weights.get("relevance", 0.7)
                    temporal_weight_coeff = self.ranking_weights.get("temporal", 0.2)
                    importance_weight = self.ranking_weights.get("importance", 0.1)
                    
                    doc["final_score"] = (
                        relevance * relevance_weight + 
                        temporal_weight * temporal_weight_coeff + 
                        importance * importance_weight
                    )
                    
                except (ValueError, TypeError):
                    doc["temporal_weight"] = 0.5
                    doc["final_score"] = doc.get("relevance_score", 0.5)
            else:
                doc["temporal_weight"] = 0.5
                doc["final_score"] = doc.get("relevance_score", 0.5)
        
        # Сортируем по финальной оценке
        docs.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return docs
    
    def _build_final_context(self, docs: List[Dict[str, Any]]) -> str:
        """Собирает финальный контекст из обработанных документов"""
        if not docs:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(docs):
            content = doc.get("content", "")
            
            # Добавляем метаданные для лучшего понимания
            metadata = doc.get("metadata", {})
            timestamp = metadata.get("timestamp", "")
            
            # Форматируем часть контекста
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromtimestamp(float(timestamp))
                    
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                    context_part = f"[{time_str}] {content}"
                except:
                    context_part = content
            else:
                context_part = content
            
            # Проверяем лимит длины
            if current_length + len(context_part) > self.max_context_length:
                # Усекаем последнюю часть
                remaining_space = self.max_context_length - current_length
                if remaining_space > 100:  # Если места достаточно
                    truncated_part = context_part[:remaining_space - 3] + "..."
                    context_parts.append(truncated_part)
                break
            
            context_parts.append(context_part)
            current_length += len(context_part) + 2  # +2 для разделителя
        
        final_context = "\n\n".join(context_parts)
        
        logger.debug(f"Built final context: {len(final_context)} characters from {len(context_parts)} parts")
        
        return final_context
    
    def get_context_stats(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Возвращает статистику обработки контекста"""
        if not docs:
            return {}
        
        extraction_methods = {}
        avg_relevance = 0
        avg_temporal_weight = 0
        
        for doc in docs:
            method = doc.get("extraction_method", "unknown")
            extraction_methods[method] = extraction_methods.get(method, 0) + 1
            
            avg_relevance += doc.get("relevance_score", 0)
            avg_temporal_weight += doc.get("temporal_weight", 0)
        
        return {
            "total_docs": len(docs),
            "extraction_methods": extraction_methods,
            "avg_relevance_score": avg_relevance / len(docs),
            "avg_temporal_weight": avg_temporal_weight / len(docs),
            "context_length": sum(len(doc.get("content", "")) for doc in docs)
        }
