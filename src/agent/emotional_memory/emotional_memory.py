"""
Основной класс эмоциональной памяти.
Интегрирует анализ эмоций, нейромодуляцию и управление эмоциональными связями.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid

from .models import (
    EmotionalFragment, EmotionalState, EmotionalLink, 
    EmotionalMemoryConfig, EmotionalMemoryStats,
    EmotionType, ModulatorType
)
from .emotion_analyzer import EmotionAnalyzer
from .neuro_modulator import NeuroModulator
from ..memory.models import MemoryFragment, MemoryLevel
from ..memory.interfaces import IMemoryStorage

logger = logging.getLogger(__name__)


class EmotionalMemory:
    """
    Основной класс эмоциональной памяти.
    
    Отвечает за:
    - Анализ эмоционального содержания фрагментов памяти
    - Применение нейромодуляции для изменения приоритетов
    - Создание и управление эмоциональными связями
    - Предоставление эмоционального контекста
    - Отслеживание эмоционального состояния агента
    """
    
    def __init__(self, storage: IMemoryStorage, config: Optional[EmotionalMemoryConfig] = None):
        self.storage = storage
        self.config = config or EmotionalMemoryConfig()
        
        # Основные компоненты
        self.emotion_analyzer = EmotionAnalyzer()
        self.neuro_modulator = NeuroModulator()
        
        # Состояние
        self.current_emotional_state = EmotionalState()
        self.emotional_fragments: Dict[str, EmotionalFragment] = {}
        self.emotional_links: Dict[str, EmotionalLink] = {}
        
        # Статистика
        self.stats = EmotionalMemoryStats(
            stats_period_start=datetime.now(),
            stats_period_end=datetime.now()
        )
        
        # Фоновые задачи
        self._cleanup_task: Optional[asyncio.Task] = None
        self._decay_task: Optional[asyncio.Task] = None
        
        logger.info("EmotionalMemory initialized")
    
    async def initialize(self) -> bool:
        """Инициализация эмоциональной памяти"""
        try:
            # Инициализируем хранилище
            if not await self.storage.init_storage():
                logger.error("Failed to initialize emotional memory storage")
                return False
            
            # Загружаем существующие эмоциональные фрагменты
            await self._load_existing_fragments()
            
            # Запускаем фоновые задачи
            await self._start_background_tasks()
            
            logger.info("EmotionalMemory initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing emotional memory: {e}")
            return False
    
    async def process_fragment(self, fragment: MemoryFragment, context: Optional[str] = None) -> MemoryFragment:
        """
        Обрабатывает фрагмент памяти через эмоциональную систему
        
        Args:
            fragment: Фрагмент памяти для обработки
            context: Дополнительный контекст
            
        Returns:
            Обработанный фрагмент с эмоциональными метаданными
        """
        try:
            # 1. Анализируем эмоции
            emotion_analysis = self.emotion_analyzer.analyze_emotion(fragment.content, context)
            
            # 2. Проверяем порог для эмоциональной обработки
            if emotion_analysis["confidence"] < self.config.emotion_detection_threshold:
                logger.debug(f"Fragment {fragment.id} below emotion detection threshold")
                return fragment
            
            # 3. Создаем эмоциональный фрагмент
            emotional_fragment = EmotionalFragment(
                memory_fragment=fragment,
                emotion_type=emotion_analysis["dominant_emotion"],
                emotion_intensity=emotion_analysis["confidence"],
                emotion_confidence=emotion_analysis["confidence"],
                emotional_weight=self._calculate_emotional_weight(emotion_analysis),
                neuro_modulators=self._extract_modulator_levels(emotion_analysis)
            )
            
            # 4. Применяем нейромодуляцию
            modulated_fragment = self.neuro_modulator.modulate_fragment(
                fragment, emotion_analysis
            )
            emotional_fragment.memory_fragment = modulated_fragment
            
            # 5. Создаем эмоциональные связи
            await self._create_emotional_links(emotional_fragment)
            
            # 6. Сохраняем эмоциональный фрагмент
            self.emotional_fragments[fragment.id] = emotional_fragment
            
            # 7. Обновляем эмоциональное состояние
            await self._update_emotional_state(emotional_fragment)
            
            # 8. Обновляем статистику
            self._update_stats(emotional_fragment)
            
            logger.debug(f"Processed emotional fragment {fragment.id}: {emotion_analysis['dominant_emotion']}")
            
            return modulated_fragment
            
        except Exception as e:
            logger.error(f"Error processing emotional fragment: {e}")
            return fragment
    
    async def get_emotional_context(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Получает эмоциональный контекст для запроса
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            Словарь с эмоциональным контекстом
        """
        try:
            # 1. Анализируем эмоции запроса
            query_emotion_analysis = self.emotion_analyzer.analyze_emotion(query)
            
            # 2. Ищем эмоционально похожие фрагменты
            similar_fragments = await self._find_emotionally_similar_fragments(
                query_emotion_analysis, limit
            )
            
            # 3. Ищем связанные фрагменты
            linked_fragments = await self._find_linked_fragments(
                query_emotion_analysis, limit
            )
            
            # 4. Получаем текущее эмоциональное состояние
            current_state = self.current_emotional_state
            
            # 5. Формируем контекст
            context = {
                "query_emotions": query_emotion_analysis,
                "similar_fragments": [
                    {
                        "content": ef.memory_fragment.content,
                        "emotion": ef.emotion_type,
                        "intensity": ef.emotion_intensity,
                        "emotional_weight": ef.emotional_weight,
                        "timestamp": ef.memory_fragment.timestamp
                    }
                    for ef in similar_fragments
                ],
                "linked_fragments": [
                    {
                        "content": ef.memory_fragment.content,
                        "emotion": ef.emotion_type,
                        "link_strength": self._get_link_strength(ef.memory_fragment.id, query),
                        "timestamp": ef.memory_fragment.timestamp
                    }
                    for ef in linked_fragments
                ],
                "current_emotional_state": {
                    "dominant_emotion": current_state.dominant_emotion,
                    "valence": current_state.overall_valence,
                    "arousal": current_state.arousal_level,
                    "context_summary": current_state.emotional_context_summary
                },
                "emotional_trends": self.emotion_analyzer.get_emotion_trends(),
                "modulator_state": self.neuro_modulator.get_current_state()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting emotional context: {e}")
            return {"error": str(e)}
    
    async def apply_feedback_reward(self, fragment_id: str, reward_strength: float, feedback_text: str):
        """
        Применяет награду на основе обратной связи пользователя
        
        Args:
            fragment_id: ID фрагмента для награждения
            reward_strength: Сила награды (-1.0 до 1.0)
            feedback_text: Текст обратной связи
        """
        try:
            # Находим эмоциональный фрагмент
            if fragment_id not in self.emotional_fragments:
                logger.warning(f"Emotional fragment {fragment_id} not found for reward")
                return
            
            emotional_fragment = self.emotional_fragments[fragment_id]
            
            # Анализируем обратную связь
            feedback_analysis = self.emotion_analyzer.analyze_emotion(feedback_text)
            
            # Применяем дофаминовую награду
            if reward_strength > 0:
                modulated_fragment = self.neuro_modulator.apply_dopamine_reward(
                    emotional_fragment.memory_fragment, reward_strength
                )
                emotional_fragment.memory_fragment = modulated_fragment
                
                # Усиливаем эмоциональный вес
                emotional_fragment.emotional_weight = min(1.0, 
                    emotional_fragment.emotional_weight * (1.0 + reward_strength * 0.3)
                )
            
            # Обновляем метаданные с информацией о награде
            if not hasattr(emotional_fragment.memory_fragment, 'metadata'):
                emotional_fragment.memory_fragment.metadata = {}
            
            emotional_fragment.memory_fragment.metadata.update({
                "feedback_reward": {
                    "strength": reward_strength,
                    "feedback_text": feedback_text,
                    "feedback_emotion": feedback_analysis["dominant_emotion"],
                    "applied_at": datetime.now().isoformat()
                }
            })
            
            # Создаем связи с похожими положительными фрагментами
            if reward_strength > 0.5:
                await self._reinforce_positive_links(emotional_fragment)
            
            logger.info(f"Applied feedback reward {reward_strength} to fragment {fragment_id}")
            
        except Exception as e:
            logger.error(f"Error applying feedback reward: {e}")
    
    async def get_emotional_summary(self, time_period_hours: int = 24) -> Dict[str, Any]:
        """Получает эмоциональную сводку за период"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_period_hours)
            
            # Фильтруем фрагменты по времени
            recent_fragments = [
                ef for ef in self.emotional_fragments.values()
                if ef.emotion_detected_at >= cutoff_time
            ]
            
            if not recent_fragments:
                return {"message": "No emotional fragments in the specified period"}
            
            # Анализируем распределение эмоций
            emotion_counts = {}
            total_intensity = 0.0
            total_weight = 0.0
            
            for ef in recent_fragments:
                emotion = ef.emotion_type
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                total_intensity += ef.emotion_intensity
                total_weight += ef.emotional_weight
            
            # Определяем доминирующие эмоции
            sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Рассчитываем средние значения
            avg_intensity = total_intensity / len(recent_fragments)
            avg_weight = total_weight / len(recent_fragments)
            
            # Анализируем тренды
            emotion_trends = self.emotion_analyzer.get_emotion_trends(time_period_hours)
            
            summary = {
                "period_hours": time_period_hours,
                "total_fragments": len(recent_fragments),
                "emotion_distribution": dict(sorted_emotions),
                "dominant_emotion": sorted_emotions[0][0] if sorted_emotions else EmotionType.NEUTRAL,
                "average_intensity": avg_intensity,
                "average_emotional_weight": avg_weight,
                "emotion_trends": emotion_trends,
                "current_state": {
                    "dominant_emotion": self.current_emotional_state.dominant_emotion,
                    "valence": self.current_emotional_state.overall_valence,
                    "arousal": self.current_emotional_state.arousal_level
                },
                "modulator_levels": self.neuro_modulator.get_current_state()["current_levels"],
                "generated_at": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating emotional summary: {e}")
            return {"error": str(e)}
    
    # Приватные методы
    
    def _calculate_emotional_weight(self, emotion_analysis: Dict) -> float:
        """Рассчитывает эмоциональный вес фрагмента"""
        base_weight = emotion_analysis["confidence"]
        intensity_bonus = emotion_analysis.get("arousal", 0.5) * 0.3
        complexity_bonus = emotion_analysis.get("emotional_complexity", 1) * 0.1
        
        weight = (base_weight + intensity_bonus + complexity_bonus) * self.config.emotional_weight_multiplier
        return min(1.0, weight)
    
    def _extract_modulator_levels(self, emotion_analysis: Dict) -> Dict[ModulatorType, float]:
        """Извлекает уровни нейромодуляторов из анализа эмоций"""
        modulator_levels = {}
        
        valence = emotion_analysis.get("valence", 0.0)
        arousal = emotion_analysis.get("arousal", 0.5)
        confidence = emotion_analysis.get("confidence", 0.0)
        
        # Дофамин - положительные эмоции и высокая уверенность
        if valence > 0.3:
            modulator_levels[ModulatorType.DOPAMINE] = min(1.0, valence * confidence)
        
        # Серотонин - стабильные эмоции
        modulator_levels[ModulatorType.SEROTONIN] = 1.0 - abs(valence)
        
        # Норэпинефрин - высокое возбуждение
        if arousal > 0.6:
            modulator_levels[ModulatorType.NOREPINEPHRINE] = arousal
        
        # Ацетилхолин - внимание и обучение
        modulator_levels[ModulatorType.ACETYLCHOLINE] = confidence
        
        # ГАМК - торможение при высоком возбуждении
        if arousal > 0.7:
            modulator_levels[ModulatorType.GABA] = arousal * 0.8
        
        return modulator_levels
    
    async def _create_emotional_links(self, emotional_fragment: EmotionalFragment):
        """Создает эмоциональные связи с существующими фрагментами"""
        try:
            current_emotion = emotional_fragment.emotion_type
            current_weight = emotional_fragment.emotional_weight
            
            # Ограничиваем количество создаваемых связей
            max_links = self.config.max_emotional_links_per_fragment
            created_links = 0
            
            for existing_id, existing_fragment in self.emotional_fragments.items():
                if created_links >= max_links:
                    break
                
                if existing_id == emotional_fragment.memory_fragment.id:
                    continue
                
                # Рассчитываем эмоциональное сходство
                similarity = self._calculate_emotional_similarity(
                    emotional_fragment, existing_fragment
                )
                
                # Создаем связь, если сходство достаточно высокое
                if similarity > 0.6:
                    link = EmotionalLink(
                        id=str(uuid.uuid4()),
                        source_fragment_id=emotional_fragment.memory_fragment.id,
                        target_fragment_id=existing_id,
                        link_type="similarity",
                        emotional_similarity=similarity,
                        link_strength=similarity * current_weight,
                        created_by="auto"
                    )
                    
                    self.emotional_links[link.id] = link
                    created_links += 1
            
            logger.debug(f"Created {created_links} emotional links for fragment {emotional_fragment.memory_fragment.id}")
            
        except Exception as e:
            logger.error(f"Error creating emotional links: {e}")
    
    def _calculate_emotional_similarity(self, fragment1: EmotionalFragment, fragment2: EmotionalFragment) -> float:
        """Рассчитывает эмоциональное сходство между фрагментами"""
        # Сходство по типу эмоции
        emotion_similarity = 1.0 if fragment1.emotion_type == fragment2.emotion_type else 0.3
        
        # Сходство по интенсивности
        intensity_diff = abs(fragment1.emotion_intensity - fragment2.emotion_intensity)
        intensity_similarity = 1.0 - intensity_diff
        
        # Сходство по эмоциональному весу
        weight_diff = abs(fragment1.emotional_weight - fragment2.emotional_weight)
        weight_similarity = 1.0 - weight_diff
        
        # Временная близость (более свежие фрагменты более похожи)
        time_diff = abs((fragment1.emotion_detected_at - fragment2.emotion_detected_at).total_seconds())
        time_similarity = max(0.0, 1.0 - time_diff / (24 * 3600))  # 24 часа = полное затухание
        
        # Взвешенное среднее
        similarity = (
            emotion_similarity * 0.4 +
            intensity_similarity * 0.25 +
            weight_similarity * 0.2 +
            time_similarity * 0.15
        )
        
        return similarity
    
    async def _find_emotionally_similar_fragments(self, emotion_analysis: Dict, limit: int) -> List[EmotionalFragment]:
        """Находит эмоционально похожие фрагменты"""
        query_emotion = emotion_analysis["dominant_emotion"]
        query_intensity = emotion_analysis["confidence"]
        
        # Сортируем фрагменты по эмоциональному сходству
        similar_fragments = []
        
        for ef in self.emotional_fragments.values():
            if ef.emotion_type == query_emotion:
                intensity_diff = abs(ef.emotion_intensity - query_intensity)
                similarity_score = 1.0 - intensity_diff
                similar_fragments.append((ef, similarity_score))
        
        # Сортируем по сходству и возвращаем топ
        similar_fragments.sort(key=lambda x: x[1], reverse=True)
        return [ef for ef, _ in similar_fragments[:limit]]
    
    async def _find_linked_fragments(self, emotion_analysis: Dict, limit: int) -> List[EmotionalFragment]:
        """Находит связанные фрагменты"""
        linked_fragments = []
        
        # Ищем связи, где текущие эмоции могут быть релевантны
        for link in self.emotional_links.values():
            if link.link_strength > 0.5:  # Только сильные связи
                target_fragment = self.emotional_fragments.get(link.target_fragment_id)
                if target_fragment:
                    linked_fragments.append((target_fragment, link.link_strength))
        
        # Сортируем по силе связи
        linked_fragments.sort(key=lambda x: x[1], reverse=True)
        return [ef for ef, _ in linked_fragments[:limit]]
    
    def _get_link_strength(self, fragment_id: str, query: str) -> float:
        """Получает силу связи для фрагмента"""
        for link in self.emotional_links.values():
            if link.source_fragment_id == fragment_id or link.target_fragment_id == fragment_id:
                return link.link_strength
        return 0.0
    
    async def _reinforce_positive_links(self, emotional_fragment: EmotionalFragment):
        """Усиливает связи с положительными фрагментами"""
        if emotional_fragment.emotion_type in [EmotionType.JOY, EmotionType.TRUST]:
            # Находим другие положительные фрагменты и усиливаем связи
            for link_id, link in self.emotional_links.items():
                if (link.source_fragment_id == emotional_fragment.memory_fragment.id or 
                    link.target_fragment_id == emotional_fragment.memory_fragment.id):
                    
                    # Усиливаем связь
                    link.link_strength = min(1.0, link.link_strength * 1.2)
                    link.activation_count += 1
                    link.last_activated = datetime.now()
    
    async def _update_emotional_state(self, emotional_fragment: EmotionalFragment):
        """Обновляет текущее эмоциональное состояние агента"""
        current_emotion = emotional_fragment.emotion_type
        intensity = emotional_fragment.emotion_intensity
        
        # Обновляем доминирующую эмоцию
        if intensity > 0.6:
            self.current_emotional_state.dominant_emotion = current_emotion
        
        # Обновляем общую валентность
        if current_emotion in [EmotionType.JOY, EmotionType.TRUST, EmotionType.ANTICIPATION]:
            self.current_emotional_state.overall_valence += intensity * 0.1
        elif current_emotion in [EmotionType.SADNESS, EmotionType.ANGER, EmotionType.FEAR, EmotionType.DISGUST]:
            self.current_emotional_state.overall_valence -= intensity * 0.1
        
        # Ограничиваем валентность
        self.current_emotional_state.overall_valence = max(-1.0, min(1.0, 
            self.current_emotional_state.overall_valence
        ))
        
        # Обновляем уровень возбуждения
        if current_emotion in [EmotionType.ANGER, EmotionType.FEAR, EmotionType.JOY, EmotionType.SURPRISE]:
            self.current_emotional_state.arousal_level = min(1.0, 
                self.current_emotional_state.arousal_level + intensity * 0.1
            )
        
        # Добавляем в недавние события
        self.current_emotional_state.recent_emotional_events.append(emotional_fragment.memory_fragment.id)
        
        # Ограничиваем размер списка недавних событий
        if len(self.current_emotional_state.recent_emotional_events) > 10:
            self.current_emotional_state.recent_emotional_events = \
                self.current_emotional_state.recent_emotional_events[-10:]
        
        # Обновляем временные метки
        self.current_emotional_state.state_timestamp = datetime.now()
    
    def _update_stats(self, emotional_fragment: EmotionalFragment):
        """Обновляет статистику эмоциональной памяти"""
        self.stats.total_emotional_fragments += 1
        
        emotion_type = emotional_fragment.emotion_type
        self.stats.emotion_distribution[emotion_type] = \
            self.stats.emotion_distribution.get(emotion_type, 0) + 1
        
        # Обновляем статистику нейромодуляторов
        for modulator_type, level in emotional_fragment.neuro_modulators.items():
            if modulator_type not in self.stats.average_modulator_levels:
                self.stats.average_modulator_levels[modulator_type] = level
            else:
                # Скользящее среднее
                current_avg = self.stats.average_modulator_levels[modulator_type]
                self.stats.average_modulator_levels[modulator_type] = \
                    (current_avg * 0.9 + level * 0.1)
            
            self.stats.modulator_activity[modulator_type] = \
                self.stats.modulator_activity.get(modulator_type, 0) + 1
        
        self.stats.last_updated = datetime.now()
    
    async def _load_existing_fragments(self):
        """Загружает существующие эмоциональные фрагменты из хранилища"""
        try:
            # Реализация зависит от типа хранилища
            # Пока оставляем заглушку
            logger.debug("Loading existing emotional fragments...")
            
        except Exception as e:
            logger.error(f"Error loading existing fragments: {e}")
    
    async def _start_background_tasks(self):
        """Запускает фоновые задачи"""
        try:
            # Задача очистки просроченных связей
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_links())
            
            # Задача естественного распада нейромодуляторов
            self._decay_task = asyncio.create_task(self._modulator_decay_loop())
            
            logger.debug("Background tasks started")
            
        except Exception as e:
            logger.error(f"Error starting background tasks: {e}")
    
    async def _cleanup_expired_links(self):
        """Очищает просроченные эмоциональные связи"""
        while True:
            try:
                await asyncio.sleep(self.config.link_cleanup_interval_hours * 3600)
                
                current_time = datetime.now()
                expired_links = []
                
                for link_id, link in self.emotional_links.items():
                    # Удаляем связи, которые не активировались долгое время
                    if link.last_activated:
                        time_since_activation = (current_time - link.last_activated).total_seconds()
                        if time_since_activation > self.config.emotional_memory_ttl_hours * 3600:
                            expired_links.append(link_id)
                
                # Удаляем просроченные связи
                for link_id in expired_links:
                    del self.emotional_links[link_id]
                
                if expired_links:
                    logger.info(f"Cleaned up {len(expired_links)} expired emotional links")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _modulator_decay_loop(self):
        """Цикл естественного распада нейромодуляторов"""
        while True:
            try:
                await asyncio.sleep(60)  # Каждую минуту
                self.neuro_modulator.decay_modulators(1)  # 1 минута
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in modulator decay loop: {e}")
    
    async def shutdown(self):
        """Завершение работы эмоциональной памяти"""
        try:
            # Отменяем фоновые задачи
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._decay_task:
                self._decay_task.cancel()
            
            logger.info("EmotionalMemory shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during emotional memory shutdown: {e}")
