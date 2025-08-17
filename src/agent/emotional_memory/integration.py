"""
Интеграция эмоциональной памяти с существующей системой агента.
Обеспечивает бесшовную интеграцию с core.py и другими компонентами.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .emotional_memory import EmotionalMemory
from .emotional_context import EmotionalContext
from .profile_corrector import ProfileCorrector
from .models import EmotionalMemoryConfig, FeedbackAnalysis
from ..memory.controller import MemoryController
from ..memory.models import MemoryFragment
from ..models import AgentProfile
from ..profile_manager import active_profiles

logger = logging.getLogger(__name__)


class EmotionalMemoryIntegration:
    """
    Основной класс интеграции эмоциональной памяти.
    
    Интегрируется с:
    - agent/core.py для обработки сообщений
    - memory/controller.py для работы с памятью
    - profile_manager.py для корректировки профилей
    """
    
    def __init__(self, memory_controller: MemoryController, 
                 config: Optional[EmotionalMemoryConfig] = None):
        self.memory_controller = memory_controller
        self.config = config or EmotionalMemoryConfig()
        
        # Основные компоненты
        self.emotional_memory: Optional[EmotionalMemory] = None
        self.emotional_context: Optional[EmotionalContext] = None
        self.profile_corrector: Optional[ProfileCorrector] = None
        
        # Состояние интеграции
        self.is_initialized = False
        self.integration_stats = {
            "messages_processed": 0,
            "feedback_analyzed": 0,
            "profiles_corrected": 0,
            "emotional_fragments_created": 0,
            "last_activity": None
        }
        
        logger.info("EmotionalMemoryIntegration created")
    
    async def initialize(self) -> bool:
        """Инициализация всех компонентов эмоциональной памяти"""
        try:
            # 1. Инициализируем эмоциональную память
            storage = self.memory_controller.storage.get_storage_for_level("L1")  # Используем L1 для эмоций
            self.emotional_memory = EmotionalMemory(storage, self.config)
            
            if not await self.emotional_memory.initialize():
                logger.error("Failed to initialize emotional memory")
                return False
            
            # 2. Инициализируем эмоциональный контекст
            self.emotional_context = EmotionalContext(self.emotional_memory)
            
            # 3. Инициализируем корректор профиля
            self.profile_corrector = ProfileCorrector(self.config)
            
            self.is_initialized = True
            logger.info("EmotionalMemoryIntegration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing emotional memory integration: {e}")
            return False
    
    async def process_user_message(self, user_message: str, user_id: str, 
                                 conversation_history: List[str] = None) -> Dict[str, Any]:
        """
        Обрабатывает сообщение пользователя через эмоциональную систему
        
        Интеграционная точка для agent/core.py
        
        Args:
            user_message: Сообщение пользователя
            user_id: ID пользователя
            conversation_history: История разговора
            
        Returns:
            Эмоциональный контекст для генерации ответа
        """
        try:
            if not self.is_initialized:
                logger.warning("Emotional memory not initialized, returning empty context")
                return {}
            
            # 1. Создаем фрагмент памяти
            fragment = MemoryFragment(
                content=user_message,
                timestamp=datetime.now().timestamp(),
                user_id=user_id,
                metadata={"source": "user_message"}
            )
            
            # 2. Обрабатываем через эмоциональную память
            processed_fragment = await self.emotional_memory.process_fragment(
                fragment, context="\n".join(conversation_history or [])
            )
            
            # 3. Получаем эмоциональный контекст
            emotional_context = await self.emotional_context.get_context_for_response(
                user_message, user_id, conversation_history
            )
            
            # 4. Обновляем статистику
            self.integration_stats["messages_processed"] += 1
            self.integration_stats["last_activity"] = datetime.now()
            
            if processed_fragment.priority != fragment.priority:
                self.integration_stats["emotional_fragments_created"] += 1
            
            logger.debug(f"Processed user message for {user_id} with emotion: {emotional_context.get('user_emotion', {}).get('type', 'unknown')}")
            
            return {
                "processed_fragment": processed_fragment,
                "emotional_context": emotional_context,
                "integration_stats": self.integration_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"Error processing user message through emotional memory: {e}")
            return {}
    
    async def process_feedback(self, user_id: str, feedback_text: str, 
                             conversation_context: List[str] = None) -> Dict[str, Any]:
        """
        Обрабатывает обратную связь пользователя и корректирует профиль
        
        Интеграционная точка для обработки реакций пользователя
        
        Args:
            user_id: ID пользователя
            feedback_text: Текст обратной связи
            conversation_context: Контекст разговора
            
        Returns:
            Результат обработки обратной связи
        """
        try:
            if not self.is_initialized:
                logger.warning("Emotional memory not initialized")
                return {}
            
            # 1. Анализируем обратную связь
            feedback_analysis = await self.profile_corrector.analyze_feedback(
                user_id, feedback_text, conversation_context or []
            )
            
            if not feedback_analysis:
                return {"status": "feedback_ignored", "reason": "insufficient_quality"}
            
            # 2. Применяем корректировки профиля
            adjustments = await self.profile_corrector.apply_corrections(
                user_id, feedback_analysis
            )
            
            # 3. Применяем эмоциональную награду/наказание
            reward_strength = self._calculate_reward_strength(feedback_analysis)
            
            # Находим релевантные фрагменты для награждения
            relevant_fragments = await self._find_relevant_fragments_for_feedback(
                user_id, conversation_context, feedback_analysis
            )
            
            for fragment_id in relevant_fragments:
                await self.emotional_memory.apply_feedback_reward(
                    fragment_id, reward_strength, feedback_text
                )
            
            # 4. Обновляем статистику
            self.integration_stats["feedback_analyzed"] += 1
            if adjustments:
                self.integration_stats["profiles_corrected"] += len(adjustments)
            self.integration_stats["last_activity"] = datetime.now()
            
            result = {
                "status": "processed",
                "feedback_analysis": {
                    "emotion": feedback_analysis.feedback_emotion,
                    "sentiment": feedback_analysis.sentiment_score,
                    "priority": feedback_analysis.feedback_priority,
                    "category": feedback_analysis.feedback_category
                },
                "adjustments_applied": len(adjustments),
                "adjustments": [
                    {
                        "field": adj.profile_field,
                        "old_value": adj.old_value,
                        "new_value": adj.new_value,
                        "reason": adj.adjustment_reason
                    }
                    for adj in adjustments
                ],
                "reward_strength": reward_strength,
                "fragments_rewarded": len(relevant_fragments)
            }
            
            logger.info(f"Processed feedback from {user_id}: {len(adjustments)} adjustments applied")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_emotional_context_for_prompt(self, user_message: str, user_id: str) -> str:
        """
        Получает эмоциональный контекст в виде текста для добавления в промпт
        
        Интеграционная точка для prompt_builder.py
        
        Args:
            user_message: Сообщение пользователя
            user_id: ID пользователя
            
        Returns:
            Текстовое описание эмоционального контекста
        """
        try:
            if not self.is_initialized:
                return ""
            
            # Получаем эмоциональный контекст (синхронно для простоты интеграции)
            # В реальной реализации лучше использовать кэш
            context_data = asyncio.run(
                self.emotional_context.get_context_for_response(user_message, user_id)
            )
            
            if not context_data:
                return ""
            
            # Формируем текстовое описание контекста
            user_emotion = context_data.get("user_emotion", {})
            recommendations = context_data.get("response_recommendations", {})
            dynamics = context_data.get("emotional_dynamics", {})
            
            context_parts = []
            
            # Информация об эмоции пользователя
            emotion_type = user_emotion.get("type", "neutral")
            emotion_intensity = user_emotion.get("intensity", 0.0)
            
            if emotion_intensity > 0.3:
                context_parts.append(f"Пользователь проявляет эмоцию: {emotion_type} (интенсивность: {emotion_intensity:.1f})")
            
            # Рекомендации по тону
            tone = recommendations.get("tone", "neutral")
            if tone != "neutral":
                context_parts.append(f"Рекомендуемый тон ответа: {tone}")
            
            # Специальные рекомендации
            if recommendations.get("show_concern"):
                context_parts.append("Проявите заботу и понимание")
            
            if recommendations.get("be_calming"):
                context_parts.append("Используйте успокаивающий тон")
            
            if recommendations.get("be_encouraging"):
                context_parts.append("Будьте поддерживающими и вдохновляющими")
            
            if recommendations.get("use_humor") and emotion_intensity < 0.7:
                context_parts.append("Уместно использовать легкий юмор")
            
            # Информация о динамике
            trajectory = dynamics.get("trajectory")
            if trajectory == "declining":
                context_parts.append("Эмоциональное состояние пользователя ухудшается - будьте особенно внимательны")
            elif trajectory == "improving":
                context_parts.append("Эмоциональное состояние пользователя улучшается")
            
            # Уровень эмпатии
            empathy_level = recommendations.get("empathy_level", 0.5)
            if empathy_level > 0.7:
                context_parts.append("Проявите высокий уровень эмпатии")
            
            if context_parts:
                return "ЭМОЦИОНАЛЬНЫЙ КОНТЕКСТ: " + " | ".join(context_parts)
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error getting emotional context for prompt: {e}")
            return ""
    
    def _calculate_reward_strength(self, feedback_analysis: FeedbackAnalysis) -> float:
        """Рассчитывает силу награды на основе анализа обратной связи"""
        
        sentiment = feedback_analysis.sentiment_score
        intensity = feedback_analysis.feedback_intensity
        confidence = feedback_analysis.confidence_level
        
        # Базовая сила награды основана на настроении
        base_reward = sentiment * confidence
        
        # Модулируем интенсивностью
        reward_strength = base_reward * intensity
        
        # Ограничиваем диапазон
        return max(-1.0, min(1.0, reward_strength))
    
    async def _find_relevant_fragments_for_feedback(self, user_id: str, 
                                                  conversation_context: List[str],
                                                  feedback_analysis: FeedbackAnalysis) -> List[str]:
        """Находит фрагменты памяти, релевантные для обратной связи"""
        
        try:
            # Простая реализация: награждаем последние фрагменты из контекста
            # В более сложной версии можно анализировать семантическое сходство
            
            relevant_fragments = []
            
            # Ищем фрагменты в эмоциональной памяти по ID пользователя
            for fragment_id, emotional_fragment in self.emotional_memory.emotional_fragments.items():
                if (emotional_fragment.memory_fragment.user_id == user_id and
                    emotional_fragment.memory_fragment.id in conversation_context[-3:]):  # Последние 3 сообщения
                    relevant_fragments.append(fragment_id)
            
            return relevant_fragments[:2]  # Максимум 2 фрагмента
            
        except Exception as e:
            logger.error(f"Error finding relevant fragments: {e}")
            return []
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Получает статистику интеграции"""
        stats = self.integration_stats.copy()
        
        if self.emotional_memory:
            emotional_stats = {
                "total_emotional_fragments": len(self.emotional_memory.emotional_fragments),
                "total_emotional_links": len(self.emotional_memory.emotional_links),
                "current_emotional_state": self.emotional_memory.current_emotional_state.dominant_emotion
            }
            stats.update(emotional_stats)
        
        if self.profile_corrector:
            correction_stats = {
                "total_feedback_analyzed": len(self.profile_corrector.feedback_history),
                "total_adjustments_made": len(self.profile_corrector.adjustment_history)
            }
            stats.update(correction_stats)
        
        return stats
    
    async def get_emotional_summary_for_user(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Получает эмоциональную сводку для пользователя"""
        try:
            if not self.is_initialized:
                return {}
            
            # Получаем общую эмоциональную сводку
            summary = await self.emotional_memory.get_emotional_summary(hours)
            
            # Получаем историю корректировок для пользователя
            if self.profile_corrector:
                correction_history = self.profile_corrector.get_correction_history(user_id, days=hours//24 or 1)
                summary["correction_history"] = correction_history
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting emotional summary: {e}")
            return {}
    
    async def shutdown(self):
        """Завершение работы интеграции"""
        try:
            if self.emotional_memory:
                await self.emotional_memory.shutdown()
            
            if self.emotional_context:
                self.emotional_context.clear_cache()
            
            logger.info("EmotionalMemoryIntegration shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during emotional memory integration shutdown: {e}")


# Глобальный экземпляр для использования в других модулях
emotional_integration: Optional[EmotionalMemoryIntegration] = None


async def initialize_emotional_memory(memory_controller: MemoryController, 
                                    config: Optional[EmotionalMemoryConfig] = None) -> bool:
    """
    Инициализирует глобальную эмоциональную память
    
    Вызывается при старте приложения
    """
    global emotional_integration
    
    try:
        emotional_integration = EmotionalMemoryIntegration(memory_controller, config)
        success = await emotional_integration.initialize()
        
        if success:
            logger.info("Global emotional memory integration initialized")
        else:
            logger.error("Failed to initialize global emotional memory integration")
        
        return success
        
    except Exception as e:
        logger.error(f"Error initializing global emotional memory: {e}")
        return False


def get_emotional_integration() -> Optional[EmotionalMemoryIntegration]:
    """Получает глобальный экземпляр эмоциональной интеграции"""
    return emotional_integration


async def shutdown_emotional_memory():
    """Завершает работу глобальной эмоциональной памяти"""
    global emotional_integration
    
    if emotional_integration:
        await emotional_integration.shutdown()
        emotional_integration = None
        logger.info("Global emotional memory integration shut down")
