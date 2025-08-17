"""
Компонент для предоставления эмоционального контекста агенту.
Интегрируется с основным процессом генерации ответов.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import EmotionType, EmotionalFragment, EmotionalState
from .emotional_memory import EmotionalMemory
from ..memory.models import MemoryFragment

logger = logging.getLogger(__name__)


class EmotionalContext:
    """
    Предоставляет эмоциональный контекст для генерации ответов агента.
    
    Отвечает за:
    - Анализ эмоционального состояния пользователя
    - Предоставление релевантного эмоционального контекста
    - Рекомендации по тону и стилю ответа
    - Мониторинг эмоциональной динамики диалога
    """
    
    def __init__(self, emotional_memory: EmotionalMemory):
        self.emotional_memory = emotional_memory
        
        # Кэш контекста для оптимизации
        self.context_cache: Dict[str, Dict] = {}
        self.cache_ttl_seconds = 300  # 5 минут
        
        logger.info("EmotionalContext initialized")
    
    async def get_context_for_response(self, user_message: str, user_id: str, 
                                     conversation_history: List[str] = None) -> Dict[str, Any]:
        """
        Получает эмоциональный контекст для генерации ответа
        
        Args:
            user_message: Сообщение пользователя
            user_id: ID пользователя
            conversation_history: История разговора
            
        Returns:
            Словарь с эмоциональным контекстом
        """
        try:
            # Проверяем кэш
            cache_key = f"{user_id}_{hash(user_message)}"
            if cache_key in self.context_cache:
                cached_context = self.context_cache[cache_key]
                if (datetime.now() - cached_context["timestamp"]).seconds < self.cache_ttl_seconds:
                    return cached_context["context"]
            
            # Получаем базовый эмоциональный контекст
            emotional_context = await self.emotional_memory.get_emotional_context(user_message)
            
            # Анализируем текущее сообщение
            current_emotion_analysis = self.emotional_memory.emotion_analyzer.analyze_emotion(user_message)
            
            # Получаем рекомендации по тону ответа
            response_recommendations = self._generate_response_recommendations(
                current_emotion_analysis, emotional_context
            )
            
            # Анализируем эмоциональную динамику
            emotional_dynamics = await self._analyze_emotional_dynamics(
                user_id, current_emotion_analysis, conversation_history
            )
            
            # Получаем персонализированные рекомендации
            personalized_recommendations = self._get_personalized_recommendations(
                user_id, current_emotion_analysis
            )
            
            # Формируем итоговый контекст
            context = {
                "user_emotion": {
                    "type": current_emotion_analysis["dominant_emotion"],
                    "intensity": current_emotion_analysis["confidence"],
                    "valence": current_emotion_analysis["valence"],
                    "arousal": current_emotion_analysis["arousal"]
                },
                "emotional_context": emotional_context,
                "response_recommendations": response_recommendations,
                "emotional_dynamics": emotional_dynamics,
                "personalized_recommendations": personalized_recommendations,
                "context_strength": self._calculate_context_strength(emotional_context),
                "generated_at": datetime.now().isoformat()
            }
            
            # Кэшируем результат
            self.context_cache[cache_key] = {
                "context": context,
                "timestamp": datetime.now()
            }
            
            # Ограничиваем размер кэша
            if len(self.context_cache) > 100:
                # Удаляем самые старые записи
                oldest_keys = sorted(
                    self.context_cache.keys(),
                    key=lambda k: self.context_cache[k]["timestamp"]
                )[:20]
                for key in oldest_keys:
                    del self.context_cache[key]
            
            logger.debug(f"Generated emotional context for {user_id}: {current_emotion_analysis['dominant_emotion']}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting emotional context: {e}")
            return self._get_default_context()
    
    def _generate_response_recommendations(self, emotion_analysis: Dict, 
                                         emotional_context: Dict) -> Dict[str, Any]:
        """Генерирует рекомендации по тону и стилю ответа"""
        
        dominant_emotion = emotion_analysis["dominant_emotion"]
        intensity = emotion_analysis["confidence"]
        valence = emotion_analysis["valence"]
        arousal = emotion_analysis["arousal"]
        
        recommendations = {
            "tone": "neutral",
            "empathy_level": 0.5,
            "formality_level": 0.5,
            "response_length": "medium",
            "use_humor": False,
            "show_concern": False,
            "be_encouraging": False,
            "be_calming": False,
            "match_energy": False
        }
        
        # Рекомендации на основе типа эмоции
        if dominant_emotion == EmotionType.JOY:
            recommendations.update({
                "tone": "enthusiastic",
                "empathy_level": 0.7,
                "use_humor": True,
                "be_encouraging": True,
                "match_energy": intensity > 0.6
            })
            
        elif dominant_emotion == EmotionType.SADNESS:
            recommendations.update({
                "tone": "compassionate",
                "empathy_level": 0.9,
                "formality_level": 0.3,
                "show_concern": True,
                "be_encouraging": True,
                "be_calming": True
            })
            
        elif dominant_emotion == EmotionType.ANGER:
            recommendations.update({
                "tone": "understanding",
                "empathy_level": 0.8,
                "formality_level": 0.6,
                "show_concern": True,
                "be_calming": True,
                "use_humor": False
            })
            
        elif dominant_emotion == EmotionType.FEAR:
            recommendations.update({
                "tone": "reassuring",
                "empathy_level": 0.9,
                "formality_level": 0.4,
                "show_concern": True,
                "be_calming": True,
                "be_encouraging": True
            })
            
        elif dominant_emotion == EmotionType.SURPRISE:
            recommendations.update({
                "tone": "engaging",
                "empathy_level": 0.6,
                "match_energy": True,
                "use_humor": intensity < 0.8  # Не шутим при сильном удивлении
            })
            
        elif dominant_emotion == EmotionType.TRUST:
            recommendations.update({
                "tone": "warm",
                "empathy_level": 0.7,
                "formality_level": 0.3,
                "be_encouraging": True
            })
            
        elif dominant_emotion == EmotionType.ANTICIPATION:
            recommendations.update({
                "tone": "supportive",
                "empathy_level": 0.6,
                "be_encouraging": True,
                "match_energy": True
            })
        
        # Корректировки на основе валентности
        if valence < -0.5:  # Сильно негативные эмоции
            recommendations.update({
                "empathy_level": min(1.0, recommendations["empathy_level"] + 0.2),
                "show_concern": True,
                "use_humor": False,
                "be_calming": True
            })
        elif valence > 0.5:  # Сильно позитивные эмоции
            recommendations.update({
                "use_humor": True,
                "be_encouraging": True,
                "match_energy": True
            })
        
        # Корректировки на основе уровня возбуждения
        if arousal > 0.7:  # Высокое возбуждение
            recommendations.update({
                "response_length": "short" if dominant_emotion in [EmotionType.ANGER, EmotionType.FEAR] else "medium",
                "be_calming": dominant_emotion in [EmotionType.ANGER, EmotionType.FEAR],
                "match_energy": dominant_emotion in [EmotionType.JOY, EmotionType.SURPRISE]
            })
        elif arousal < 0.3:  # Низкое возбуждение
            recommendations.update({
                "tone": "gentle",
                "response_length": "long",
                "be_encouraging": True
            })
        
        # Учитываем эмоциональный контекст из памяти
        current_state = emotional_context.get("current_emotional_state", {})
        if current_state.get("valence", 0) < -0.3:
            # Если общее эмоциональное состояние негативное, будем более осторожными
            recommendations.update({
                "empathy_level": min(1.0, recommendations["empathy_level"] + 0.1),
                "use_humor": False,
                "show_concern": True
            })
        
        return recommendations
    
    async def _analyze_emotional_dynamics(self, user_id: str, current_emotion: Dict,
                                        conversation_history: List[str] = None) -> Dict[str, Any]:
        """Анализирует эмоциональную динамику диалога"""
        
        try:
            # Получаем недавнюю эмоциональную историю
            recent_summary = await self.emotional_memory.get_emotional_summary(time_period_hours=1)
            
            # Анализируем тренды
            emotion_trends = self.emotional_memory.emotion_analyzer.get_emotion_trends(hours=2)
            
            # Определяем эмоциональную траекторию
            trajectory = self._determine_emotional_trajectory(current_emotion, recent_summary)
            
            # Анализируем стабильность эмоций
            stability = self._calculate_emotional_stability(recent_summary)
            
            # Определяем критические моменты
            critical_moments = self._identify_critical_moments(recent_summary)
            
            dynamics = {
                "trajectory": trajectory,  # "improving", "declining", "stable", "volatile"
                "stability_score": stability,  # 0-1, где 1 = очень стабильно
                "recent_trend": emotion_trends.get("trend", EmotionType.NEUTRAL),
                "dominant_emotions_recent": emotion_trends.get("dominant_emotions", []),
                "critical_moments": critical_moments,
                "emotional_shift_detected": self._detect_emotional_shift(current_emotion, recent_summary),
                "recovery_indicators": self._detect_recovery_indicators(recent_summary),
                "escalation_risk": self._assess_escalation_risk(current_emotion, recent_summary)
            }
            
            return dynamics
            
        except Exception as e:
            logger.error(f"Error analyzing emotional dynamics: {e}")
            return {"trajectory": "unknown", "stability_score": 0.5}
    
    def _get_personalized_recommendations(self, user_id: str, emotion_analysis: Dict) -> Dict[str, Any]:
        """Получает персонализированные рекомендации на основе истории пользователя"""
        
        # Базовые рекомендации (можно расширить на основе истории пользователя)
        recommendations = {
            "preferred_communication_style": "adaptive",
            "emotional_sensitivity_level": 0.7,
            "humor_appropriateness": 0.5,
            "formality_preference": 0.5,
            "response_detail_level": 0.7,
            "empathy_emphasis": 0.6
        }
        
        # TODO: Здесь можно добавить анализ истории пользователя
        # для более точной персонализации
        
        return recommendations
    
    def _calculate_context_strength(self, emotional_context: Dict) -> float:
        """Рассчитывает силу эмоционального контекста"""
        
        strength = 0.0
        
        # Учитываем количество похожих фрагментов
        similar_fragments = emotional_context.get("similar_fragments", [])
        strength += min(0.4, len(similar_fragments) * 0.1)
        
        # Учитываем силу связей
        linked_fragments = emotional_context.get("linked_fragments", [])
        if linked_fragments:
            avg_link_strength = sum(f.get("link_strength", 0) for f in linked_fragments) / len(linked_fragments)
            strength += avg_link_strength * 0.3
        
        # Учитываем текущее эмоциональное состояние
        current_state = emotional_context.get("current_emotional_state", {})
        if abs(current_state.get("valence", 0)) > 0.5:
            strength += 0.3
        
        return min(1.0, strength)
    
    def _determine_emotional_trajectory(self, current_emotion: Dict, recent_summary: Dict) -> str:
        """Определяет эмоциональную траекторию"""
        
        current_valence = current_emotion.get("valence", 0)
        recent_valence = recent_summary.get("current_state", {}).get("valence", 0)
        
        if current_valence > recent_valence + 0.2:
            return "improving"
        elif current_valence < recent_valence - 0.2:
            return "declining"
        elif abs(current_valence - recent_valence) < 0.1:
            return "stable"
        else:
            return "volatile"
    
    def _calculate_emotional_stability(self, recent_summary: Dict) -> float:
        """Рассчитывает стабильность эмоций"""
        
        emotion_distribution = recent_summary.get("emotion_distribution", {})
        
        if not emotion_distribution:
            return 0.5
        
        # Чем более равномерно распределены эмоции, тем менее стабильно
        total_fragments = sum(emotion_distribution.values())
        if total_fragments == 0:
            return 0.5
        
        # Рассчитываем энтропию распределения эмоций
        entropy = 0.0
        for count in emotion_distribution.values():
            if count > 0:
                p = count / total_fragments
                entropy -= p * (p.bit_length() - 1) if p > 0 else 0
        
        # Нормализуем энтропию к диапазону 0-1 (инвертируем для стабильности)
        max_entropy = (len(emotion_distribution).bit_length() - 1) if emotion_distribution else 1
        stability = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.5
        
        return stability
    
    def _identify_critical_moments(self, recent_summary: Dict) -> List[Dict]:
        """Идентифицирует критические эмоциональные моменты"""
        
        critical_moments = []
        
        # Анализируем распределение эмоций
        emotion_distribution = recent_summary.get("emotion_distribution", {})
        total_fragments = sum(emotion_distribution.values())
        
        if total_fragments > 0:
            # Критический момент: много негативных эмоций
            negative_emotions = [EmotionType.SADNESS, EmotionType.ANGER, EmotionType.FEAR, EmotionType.DISGUST]
            negative_count = sum(emotion_distribution.get(emotion, 0) for emotion in negative_emotions)
            
            if negative_count / total_fragments > 0.6:
                critical_moments.append({
                    "type": "high_negativity",
                    "severity": negative_count / total_fragments,
                    "description": "High concentration of negative emotions detected"
                })
            
            # Критический момент: резкие эмоциональные изменения
            if recent_summary.get("average_intensity", 0) > 0.8:
                critical_moments.append({
                    "type": "high_intensity",
                    "severity": recent_summary.get("average_intensity", 0),
                    "description": "High emotional intensity detected"
                })
        
        return critical_moments
    
    def _detect_emotional_shift(self, current_emotion: Dict, recent_summary: Dict) -> bool:
        """Определяет, произошел ли значительный эмоциональный сдвиг"""
        
        current_valence = current_emotion.get("valence", 0)
        recent_valence = recent_summary.get("current_state", {}).get("valence", 0)
        
        # Значительный сдвиг, если изменение валентности больше 0.4
        return abs(current_valence - recent_valence) > 0.4
    
    def _detect_recovery_indicators(self, recent_summary: Dict) -> List[str]:
        """Определяет индикаторы эмоционального восстановления"""
        
        indicators = []
        
        current_valence = recent_summary.get("current_state", {}).get("valence", 0)
        
        if current_valence > 0.2:
            indicators.append("positive_valence_trend")
        
        # Проверяем наличие положительных эмоций в недавней истории
        emotion_distribution = recent_summary.get("emotion_distribution", {})
        positive_emotions = [EmotionType.JOY, EmotionType.TRUST, EmotionType.ANTICIPATION]
        positive_count = sum(emotion_distribution.get(emotion, 0) for emotion in positive_emotions)
        total_fragments = sum(emotion_distribution.values())
        
        if total_fragments > 0 and positive_count / total_fragments > 0.3:
            indicators.append("positive_emotions_present")
        
        return indicators
    
    def _assess_escalation_risk(self, current_emotion: Dict, recent_summary: Dict) -> float:
        """Оценивает риск эмоциональной эскалации"""
        
        risk = 0.0
        
        # Высокий уровень возбуждения увеличивает риск
        arousal = current_emotion.get("arousal", 0.5)
        if arousal > 0.7:
            risk += 0.3
        
        # Негативные эмоции увеличивают риск
        valence = current_emotion.get("valence", 0)
        if valence < -0.5:
            risk += 0.4
        
        # Гнев особенно увеличивает риск эскалации
        if current_emotion.get("dominant_emotion") == EmotionType.ANGER:
            risk += 0.3
        
        # Недавняя история негативных эмоций увеличивает риск
        recent_valence = recent_summary.get("current_state", {}).get("valence", 0)
        if recent_valence < -0.3:
            risk += 0.2
        
        return min(1.0, risk)
    
    def _get_default_context(self) -> Dict[str, Any]:
        """Возвращает контекст по умолчанию при ошибках"""
        return {
            "user_emotion": {
                "type": EmotionType.NEUTRAL,
                "intensity": 0.0,
                "valence": 0.0,
                "arousal": 0.5
            },
            "response_recommendations": {
                "tone": "neutral",
                "empathy_level": 0.5,
                "formality_level": 0.5,
                "response_length": "medium",
                "use_humor": False,
                "show_concern": False,
                "be_encouraging": False,
                "be_calming": False,
                "match_energy": False
            },
            "emotional_dynamics": {
                "trajectory": "unknown",
                "stability_score": 0.5
            },
            "context_strength": 0.0,
            "generated_at": datetime.now().isoformat(),
            "error": "Failed to generate emotional context"
        }
    
    def clear_cache(self):
        """Очищает кэш контекста"""
        self.context_cache.clear()
        logger.info("Emotional context cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Получает статистику кэша"""
        return {
            "cache_size": len(self.context_cache),
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "oldest_entry": min(
                (entry["timestamp"] for entry in self.context_cache.values()),
                default=None
            ),
            "newest_entry": max(
                (entry["timestamp"] for entry in self.context_cache.values()),
                default=None
            )
        }
