"""
Корректор профиля агента на основе эмоциональной обратной связи.
Автоматически адаптирует поведение агента на основе реакций пользователя.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json

from .models import (
    FeedbackAnalysis, ProfileAdjustment, EmotionType,
    EmotionalMemoryConfig
)
from .emotion_analyzer import EmotionAnalyzer
from ..models import AgentProfile
from ..profile_manager import active_profiles

logger = logging.getLogger(__name__)


class ProfileCorrector:
    """
    Корректор профиля агента на основе эмоциональной обратной связи.
    
    Анализирует обратную связь пользователя и автоматически корректирует:
    - Параметры генерации (temperature, max_tokens)
    - Стиль общения (tone, communication_style)
    - Черты личности (personality_traits)
    - Системные инструкции (system_prompt)
    """
    
    def __init__(self, config: Optional[EmotionalMemoryConfig] = None):
        self.config = config or EmotionalMemoryConfig()
        self.emotion_analyzer = EmotionAnalyzer()
        
        # История анализа обратной связи
        self.feedback_history: List[FeedbackAnalysis] = []
        
        # История корректировок профиля
        self.adjustment_history: List[ProfileAdjustment] = []
        
        # Кэш эффективности корректировок
        self.effectiveness_cache: Dict[str, float] = {}
        
        # Правила корректировки
        self.correction_rules = self._init_correction_rules()
        
        logger.info("ProfileCorrector initialized")
    
    def _init_correction_rules(self) -> Dict[str, Dict]:
        """Инициализация правил корректировки профиля"""
        return {
            # Правила для temperature (креативность)
            "temperature": {
                "increase_triggers": [
                    "скучно", "банально", "предсказуемо", "однообразно",
                    "не креативно", "не оригинально", "шаблонно"
                ],
                "decrease_triggers": [
                    "странно", "непонятно", "бред", "бессмыслица",
                    "слишком креативно", "хаотично"
                ],
                "adjustment_step": 0.1,
                "min_value": 0.1,
                "max_value": 1.0
            },
            
            # Правила для max_tokens (длина ответов)
            "max_tokens": {
                "increase_triggers": [
                    "коротко", "мало", "подробнее", "развернуто",
                    "больше информации", "недостаточно"
                ],
                "decrease_triggers": [
                    "длинно", "много", "кратко", "короче",
                    "слишком много текста", "многословно"
                ],
                "adjustment_step": 200,
                "min_value": 100,
                "max_value": 4000
            },
            
            # Правила для tone (тон общения)
            "tone": {
                "formal_triggers": [
                    "официально", "формально", "серьёзно", "профессионально",
                    "деловой стиль", "без шуток"
                ],
                "friendly_triggers": [
                    "дружелюбно", "неформально", "по-простому", "как друг",
                    "расслабленно", "легко"
                ],
                "professional_triggers": [
                    "профессионально", "экспертно", "компетентно",
                    "как специалист", "авторитетно"
                ],
                "creative_triggers": [
                    "креативно", "творчески", "нестандартно", "оригинально",
                    "с фантазией", "артистично"
                ]
            },
            
            # Правила для personality_traits (черты личности)
            "personality_traits": {
                "add_humor": [
                    "смешно", "с юмором", "весело", "шутливо",
                    "забавно", "остроумно"
                ],
                "reduce_humor": [
                    "серьёзно", "без шуток", "не смешно",
                    "неуместно", "не к месту"
                ],
                "add_empathy": [
                    "понимающе", "сочувственно", "эмпатично",
                    "с пониманием", "сопереживать"
                ],
                "add_confidence": [
                    "уверенно", "решительно", "твёрдо",
                    "без сомнений", "категорично"
                ]
            }
        }
    
    async def analyze_feedback(self, user_id: str, feedback_text: str, 
                              conversation_context: List[str]) -> FeedbackAnalysis:
        """
        Анализирует обратную связь пользователя
        
        Args:
            user_id: ID пользователя
            feedback_text: Текст обратной связи
            conversation_context: Контекст разговора (ID сообщений)
            
        Returns:
            Анализ обратной связи
        """
        try:
            # Проверяем минимальную длину обратной связи
            if len(feedback_text) < self.config.minimum_feedback_length:
                logger.debug(f"Feedback too short: {len(feedback_text)} chars")
                return None
            
            # Анализируем эмоции обратной связи
            emotion_analysis = self.emotion_analyzer.analyze_emotion(feedback_text)
            
            # Определяем категорию и аспект обратной связи
            category, aspect = self._categorize_feedback(feedback_text)
            
            # Генерируем предлагаемые корректировки
            suggested_adjustments = self._generate_adjustment_suggestions(
                feedback_text, emotion_analysis, category, aspect
            )
            
            # Рассчитываем приоритет обратной связи
            priority = self._calculate_feedback_priority(emotion_analysis, category)
            
            # Создаем анализ обратной связи
            feedback_analysis = FeedbackAnalysis(
                user_id=user_id,
                feedback_text=feedback_text,
                feedback_emotion=emotion_analysis["dominant_emotion"],
                feedback_intensity=emotion_analysis["confidence"],
                sentiment_score=emotion_analysis["valence"],
                feedback_category=category,
                feedback_aspect=aspect,
                conversation_context=conversation_context,
                suggested_adjustments=suggested_adjustments,
                confidence_level=emotion_analysis["confidence"],
                feedback_priority=priority,
                requires_immediate_action=priority > 0.8 and emotion_analysis["confidence"] > 0.7
            )
            
            # Сохраняем в историю
            self.feedback_history.append(feedback_analysis)
            
            # Ограничиваем размер истории
            if len(self.feedback_history) > 100:
                self.feedback_history = self.feedback_history[-100:]
            
            logger.info(f"Analyzed feedback from {user_id}: {category}/{aspect} (priority: {priority:.2f})")
            
            return feedback_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing feedback: {e}")
            return None
    
    async def apply_corrections(self, user_id: str, feedback_analysis: FeedbackAnalysis) -> List[ProfileAdjustment]:
        """
        Применяет корректировки профиля на основе анализа обратной связи
        
        Args:
            user_id: ID пользователя
            feedback_analysis: Анализ обратной связи
            
        Returns:
            Список примененных корректировок
        """
        try:
            if not feedback_analysis or feedback_analysis.confidence_level < self.config.adjustment_confidence_threshold:
                logger.debug("Feedback confidence too low for adjustments")
                return []
            
            # Получаем текущий профиль пользователя
            current_profile = active_profiles.get(user_id)
            if not current_profile:
                logger.warning(f"No active profile found for user {user_id}")
                return []
            
            # Проверяем лимит корректировок за день
            if not self._check_adjustment_limits(user_id):
                logger.info(f"Daily adjustment limit reached for user {user_id}")
                return []
            
            applied_adjustments = []
            
            # Применяем каждую предложенную корректировку
            for adjustment_suggestion in feedback_analysis.suggested_adjustments:
                adjustment = await self._create_profile_adjustment(
                    user_id, current_profile, adjustment_suggestion, feedback_analysis
                )
                
                if adjustment:
                    # Применяем корректировку
                    success = await self._apply_adjustment(current_profile, adjustment)
                    
                    if success:
                        adjustment.is_applied = True
                        adjustment.applied_at = datetime.now()
                        applied_adjustments.append(adjustment)
                        
                        # Сохраняем в историю
                        self.adjustment_history.append(adjustment)
                        
                        logger.info(f"Applied adjustment: {adjustment.profile_field} -> {adjustment.new_value}")
            
            # Обновляем профиль в активной памяти
            if applied_adjustments:
                active_profiles.set(user_id, current_profile)
            
            return applied_adjustments
            
        except Exception as e:
            logger.error(f"Error applying corrections: {e}")
            return []
    
    def _categorize_feedback(self, feedback_text: str) -> Tuple[str, str]:
        """Категоризирует обратную связь по типу и аспекту"""
        feedback_lower = feedback_text.lower()
        
        # Категории обратной связи
        if any(word in feedback_lower for word in ["личность", "характер", "стиль", "манера"]):
            category = "personality"
        elif any(word in feedback_lower for word in ["ответ", "реакция", "сказал", "написал"]):
            category = "response_style"
        elif any(word in feedback_lower for word in ["поведение", "действие", "делаешь"]):
            category = "behavior"
        else:
            category = "general"
        
        # Аспекты обратной связи
        if any(word in feedback_lower for word in ["тон", "интонация", "звучит"]):
            aspect = "tone"
        elif any(word in feedback_lower for word in ["юмор", "шутки", "смешно", "весело"]):
            aspect = "humor"
        elif any(word in feedback_lower for word in ["помощь", "полезно", "помогаешь"]):
            aspect = "helpfulness"
        elif any(word in feedback_lower for word in ["длинно", "коротко", "много", "мало"]):
            aspect = "response_length"
        elif any(word in feedback_lower for word in ["креативно", "оригинально", "творчески"]):
            aspect = "creativity"
        elif any(word in feedback_lower for word in ["понятно", "ясно", "понимаю"]):
            aspect = "clarity"
        else:
            aspect = "general"
        
        return category, aspect
    
    def _generate_adjustment_suggestions(self, feedback_text: str, emotion_analysis: Dict, 
                                       category: str, aspect: str) -> List[str]:
        """Генерирует предложения по корректировке профиля"""
        suggestions = []
        feedback_lower = feedback_text.lower()
        
        # Корректировки для temperature
        if any(trigger in feedback_lower for trigger in self.correction_rules["temperature"]["increase_triggers"]):
            suggestions.append("increase_temperature")
        elif any(trigger in feedback_lower for trigger in self.correction_rules["temperature"]["decrease_triggers"]):
            suggestions.append("decrease_temperature")
        
        # Корректировки для max_tokens
        if any(trigger in feedback_lower for trigger in self.correction_rules["max_tokens"]["increase_triggers"]):
            suggestions.append("increase_max_tokens")
        elif any(trigger in feedback_lower for trigger in self.correction_rules["max_tokens"]["decrease_triggers"]):
            suggestions.append("decrease_max_tokens")
        
        # Корректировки для tone
        if any(trigger in feedback_lower for trigger in self.correction_rules["tone"]["formal_triggers"]):
            suggestions.append("set_tone_formal")
        elif any(trigger in feedback_lower for trigger in self.correction_rules["tone"]["friendly_triggers"]):
            suggestions.append("set_tone_friendly")
        elif any(trigger in feedback_lower for trigger in self.correction_rules["tone"]["professional_triggers"]):
            suggestions.append("set_tone_professional")
        elif any(trigger in feedback_lower for trigger in self.correction_rules["tone"]["creative_triggers"]):
            suggestions.append("set_tone_creative")
        
        # Корректировки для personality_traits
        if any(trigger in feedback_lower for trigger in self.correction_rules["personality_traits"]["add_humor"]):
            suggestions.append("add_humor_trait")
        elif any(trigger in feedback_lower for trigger in self.correction_rules["personality_traits"]["reduce_humor"]):
            suggestions.append("reduce_humor_trait")
        elif any(trigger in feedback_lower for trigger in self.correction_rules["personality_traits"]["add_empathy"]):
            suggestions.append("add_empathy_trait")
        elif any(trigger in feedback_lower for trigger in self.correction_rules["personality_traits"]["add_confidence"]):
            suggestions.append("add_confidence_trait")
        
        return suggestions
    
    def _calculate_feedback_priority(self, emotion_analysis: Dict, category: str) -> float:
        """Рассчитывает приоритет обратной связи"""
        base_priority = emotion_analysis["confidence"]
        
        # Увеличиваем приоритет для негативных эмоций
        if emotion_analysis["valence"] < -0.3:
            base_priority *= 1.5
        
        # Увеличиваем приоритет для категорий, критичных для пользовательского опыта
        if category in ["personality", "response_style"]:
            base_priority *= 1.2
        
        # Увеличиваем приоритет для высокого эмоционального возбуждения
        if emotion_analysis["arousal"] > 0.7:
            base_priority *= 1.3
        
        return min(1.0, base_priority)
    
    async def _create_profile_adjustment(self, user_id: str, profile: AgentProfile, 
                                       suggestion: str, feedback_analysis: FeedbackAnalysis) -> Optional[ProfileAdjustment]:
        """Создает корректировку профиля"""
        try:
            adjustment_id = f"adj_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if suggestion == "increase_temperature":
                old_value = float(profile.temperature)
                new_value = min(self.correction_rules["temperature"]["max_value"], 
                              old_value + self.correction_rules["temperature"]["adjustment_step"])
                
                return ProfileAdjustment(
                    adjustment_id=adjustment_id,
                    user_id=user_id,
                    profile_field="temperature",
                    old_value=old_value,
                    new_value=new_value,
                    adjustment_type="increment",
                    based_on_feedback=[],  # Будет заполнено позже
                    adjustment_reason="User feedback indicates need for more creativity",
                    confidence_score=feedback_analysis.confidence_level
                )
            
            elif suggestion == "decrease_temperature":
                old_value = float(profile.temperature)
                new_value = max(self.correction_rules["temperature"]["min_value"],
                              old_value - self.correction_rules["temperature"]["adjustment_step"])
                
                return ProfileAdjustment(
                    adjustment_id=adjustment_id,
                    user_id=user_id,
                    profile_field="temperature",
                    old_value=old_value,
                    new_value=new_value,
                    adjustment_type="decrement",
                    based_on_feedback=[],
                    adjustment_reason="User feedback indicates responses are too chaotic",
                    confidence_score=feedback_analysis.confidence_level
                )
            
            elif suggestion == "increase_max_tokens":
                old_value = profile.max_tokens
                new_value = min(self.correction_rules["max_tokens"]["max_value"],
                              old_value + self.correction_rules["max_tokens"]["adjustment_step"])
                
                return ProfileAdjustment(
                    adjustment_id=adjustment_id,
                    user_id=user_id,
                    profile_field="max_tokens",
                    old_value=old_value,
                    new_value=new_value,
                    adjustment_type="increment",
                    based_on_feedback=[],
                    adjustment_reason="User feedback indicates need for longer responses",
                    confidence_score=feedback_analysis.confidence_level
                )
            
            elif suggestion == "decrease_max_tokens":
                old_value = profile.max_tokens
                new_value = max(self.correction_rules["max_tokens"]["min_value"],
                              old_value - self.correction_rules["max_tokens"]["adjustment_step"])
                
                return ProfileAdjustment(
                    adjustment_id=adjustment_id,
                    user_id=user_id,
                    profile_field="max_tokens",
                    old_value=old_value,
                    new_value=new_value,
                    adjustment_type="decrement",
                    based_on_feedback=[],
                    adjustment_reason="User feedback indicates responses are too long",
                    confidence_score=feedback_analysis.confidence_level
                )
            
            elif suggestion.startswith("set_tone_"):
                tone_value = suggestion.replace("set_tone_", "")
                old_value = profile.tone
                
                return ProfileAdjustment(
                    adjustment_id=adjustment_id,
                    user_id=user_id,
                    profile_field="tone",
                    old_value=old_value,
                    new_value=tone_value,
                    adjustment_type="replace",
                    based_on_feedback=[],
                    adjustment_reason=f"User feedback indicates preference for {tone_value} tone",
                    confidence_score=feedback_analysis.confidence_level
                )
            
            elif suggestion.endswith("_trait"):
                # Корректировки personality_traits требуют работы с JSON
                old_traits = json.loads(profile.personality_traits or "[]")
                new_traits = old_traits.copy()
                
                if suggestion == "add_humor_trait" and "с юмором" not in new_traits:
                    new_traits.append("с юмором")
                elif suggestion == "reduce_humor_trait" and "с юмором" in new_traits:
                    new_traits.remove("с юмором")
                elif suggestion == "add_empathy_trait" and "эмпатичная" not in new_traits:
                    new_traits.append("эмпатичная")
                elif suggestion == "add_confidence_trait" and "уверенная" not in new_traits:
                    new_traits.append("уверенная")
                
                return ProfileAdjustment(
                    adjustment_id=adjustment_id,
                    user_id=user_id,
                    profile_field="personality_traits",
                    old_value=old_traits,
                    new_value=new_traits,
                    adjustment_type="replace",
                    based_on_feedback=[],
                    adjustment_reason=f"User feedback indicates need to adjust personality traits",
                    confidence_score=feedback_analysis.confidence_level
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating profile adjustment: {e}")
            return None
    
    async def _apply_adjustment(self, profile: AgentProfile, adjustment: ProfileAdjustment) -> bool:
        """Применяет корректировку к профилю"""
        try:
            field_name = adjustment.profile_field
            new_value = adjustment.new_value
            
            # Применяем изменение к профилю
            if hasattr(profile, field_name):
                if field_name == "personality_traits":
                    # Для JSON полей нужна специальная обработка
                    setattr(profile, field_name, json.dumps(new_value, ensure_ascii=False))
                else:
                    setattr(profile, field_name, new_value)
                
                logger.debug(f"Applied adjustment: {field_name} = {new_value}")
                return True
            else:
                logger.warning(f"Profile field {field_name} does not exist")
                return False
                
        except Exception as e:
            logger.error(f"Error applying adjustment: {e}")
            return False
    
    def _check_adjustment_limits(self, user_id: str) -> bool:
        """Проверяет лимиты корректировок за день"""
        today = datetime.now().date()
        
        # Считаем корректировки за сегодня
        today_adjustments = [
            adj for adj in self.adjustment_history
            if adj.user_id == user_id and adj.created_at.date() == today
        ]
        
        return len(today_adjustments) < self.config.max_adjustments_per_day
    
    def get_correction_history(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Получает историю корректировок для пользователя"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        user_adjustments = [
            adj for adj in self.adjustment_history
            if adj.user_id == user_id and adj.created_at >= cutoff_date
        ]
        
        # Группируем по полям профиля
        field_changes = {}
        for adj in user_adjustments:
            field = adj.profile_field
            if field not in field_changes:
                field_changes[field] = []
            
            field_changes[field].append({
                "timestamp": adj.created_at.isoformat(),
                "old_value": adj.old_value,
                "new_value": adj.new_value,
                "reason": adj.adjustment_reason,
                "effectiveness": adj.effectiveness_score
            })
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_adjustments": len(user_adjustments),
            "successful_adjustments": len([adj for adj in user_adjustments if adj.is_applied]),
            "field_changes": field_changes,
            "recent_feedback_count": len([
                fb for fb in self.feedback_history
                if fb.user_id == user_id and fb.analysis_timestamp >= cutoff_date
            ])
        }
    
    async def evaluate_adjustment_effectiveness(self, adjustment: ProfileAdjustment, 
                                              post_adjustment_feedback: List[FeedbackAnalysis]) -> float:
        """Оценивает эффективность примененной корректировки"""
        try:
            if not post_adjustment_feedback:
                return 0.5  # Нейтральная оценка при отсутствии данных
            
            # Анализируем обратную связь после корректировки
            positive_feedback = 0
            negative_feedback = 0
            total_intensity = 0
            
            for feedback in post_adjustment_feedback:
                if feedback.sentiment_score > 0.2:
                    positive_feedback += 1
                elif feedback.sentiment_score < -0.2:
                    negative_feedback += 1
                
                total_intensity += abs(feedback.sentiment_score)
            
            if not post_adjustment_feedback:
                return 0.5
            
            # Рассчитываем эффективность
            total_feedback = len(post_adjustment_feedback)
            positive_ratio = positive_feedback / total_feedback
            negative_ratio = negative_feedback / total_feedback
            avg_intensity = total_intensity / total_feedback
            
            # Эффективность = (позитивная обратная связь - негативная) с учетом интенсивности
            effectiveness = (positive_ratio - negative_ratio) * avg_intensity
            effectiveness = max(0.0, min(1.0, (effectiveness + 1.0) / 2.0))  # Нормализуем к 0-1
            
            # Обновляем эффективность корректировки
            adjustment.effectiveness_score = effectiveness
            adjustment.user_satisfaction_change = positive_ratio - negative_ratio
            
            # Кэшируем результат
            self.effectiveness_cache[adjustment.adjustment_id] = effectiveness
            
            logger.info(f"Adjustment {adjustment.adjustment_id} effectiveness: {effectiveness:.2f}")
            
            return effectiveness
            
        except Exception as e:
            logger.error(f"Error evaluating adjustment effectiveness: {e}")
            return 0.5
