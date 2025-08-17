"""
Анализатор эмоций для системы эмоциональной памяти.
Расширенная версия базового анализатора эмоций с поддержкой интенсивности и контекста.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

from .models import EmotionType, EmotionIntensity, EmotionalState

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """
    Расширенный анализатор эмоций с поддержкой:
    - Множественных эмоций в тексте
    - Интенсивности эмоций
    - Контекстного анализа
    - Временной динамики эмоций
    """
    
    def __init__(self):
        self.emotion_lexicons = self._init_emotion_lexicons()
        self.intensity_modifiers = self._init_intensity_modifiers()
        self.negation_words = {"не", "нет", "никогда", "нисколько", "отнюдь", "вовсе"}
        self.amplifiers = {"очень", "крайне", "чрезвычайно", "невероятно", "супер", "мега"}
        self.diminishers = {"немного", "слегка", "чуть", "едва", "почти", "практически"}
        
        # История эмоций для контекстного анализа
        self.emotion_history: List[Tuple[datetime, EmotionType, float]] = []
        self.max_history_size = 50
    
    def _init_emotion_lexicons(self) -> Dict[EmotionType, Dict[str, float]]:
        """Инициализация словарей эмоций с весами"""
        return {
            EmotionType.JOY: {
                # Сильная радость
                "восторг": 0.9, "счастье": 0.9, "блаженство": 0.9, "эйфория": 1.0,
                "ликование": 0.9, "экстаз": 1.0, "упоение": 0.8,
                # Умеренная радость
                "радость": 0.8, "веселье": 0.7, "довольство": 0.6, "удовлетворение": 0.6,
                "приятно": 0.6, "хорошо": 0.5, "отлично": 0.8, "прекрасно": 0.8,
                "замечательно": 0.8, "великолепно": 0.9, "чудесно": 0.8,
                # Слабая радость
                "улыбка": 0.4, "смех": 0.6, "смешно": 0.5, "забавно": 0.5,
                "нравится": 0.6, "люблю": 0.7, "обожаю": 0.8, "кайф": 0.7,
                # Позитивные оценки
                "супер": 0.8, "класс": 0.7, "круто": 0.7, "офигенно": 0.8,
                "потрясающе": 0.9, "шикарно": 0.8, "божественно": 0.9
            },
            
            EmotionType.SADNESS: {
                # Сильная грусть
                "горе": 0.9, "скорбь": 0.9, "отчаяние": 1.0, "депрессия": 0.9,
                "тоска": 0.8, "печаль": 0.8, "уныние": 0.7, "меланхолия": 0.7,
                # Умеренная грусть
                "грусть": 0.7, "грустно": 0.7, "расстройство": 0.6, "огорчение": 0.6,
                "разочарование": 0.7, "сожаление": 0.6, "жалость": 0.5,
                # Слабая грусть
                "плохо": 0.5, "неприятно": 0.5, "досадно": 0.4, "жаль": 0.5,
                "слёзы": 0.7, "плач": 0.8, "рыдания": 0.9,
                # Потери и лишения
                "потеря": 0.7, "утрата": 0.8, "лишение": 0.6, "разлука": 0.7
            },
            
            EmotionType.ANGER: {
                # Сильная злость
                "ярость": 1.0, "бешенство": 1.0, "гнев": 0.9, "неистовство": 1.0,
                "остервенение": 1.0, "исступление": 1.0,
                # Умеренная злость
                "злость": 0.8, "злой": 0.8, "раздражение": 0.6, "досада": 0.5,
                "недовольство": 0.5, "возмущение": 0.7, "негодование": 0.7,
                # Агрессия
                "агрессия": 0.8, "враждебность": 0.7, "ненависть": 0.9,
                "отвращение": 0.7, "презрение": 0.6,
                # Выражения злости
                "бесит": 0.8, "раздражает": 0.6, "злюсь": 0.8, "взбешён": 0.9,
                "сердитый": 0.6, "рассерженный": 0.7, "взбешенный": 0.9,
                # Ругательства (мягкие)
                "чёрт": 0.6, "блин": 0.4, "капец": 0.7, "ужас": 0.6
            },
            
            EmotionType.FEAR: {
                # Сильный страх
                "ужас": 1.0, "кошмар": 0.9, "паника": 1.0, "террор": 1.0,
                "испуг": 0.7, "шок": 0.8, "оцепенение": 0.8,
                # Умеренный страх
                "страх": 0.8, "боязнь": 0.7, "опасение": 0.5, "тревога": 0.6,
                "беспокойство": 0.5, "волнение": 0.4, "нервозность": 0.6,
                # Слабый страх
                "переживание": 0.4, "сомнение": 0.3, "неуверенность": 0.4,
                "боюсь": 0.7, "страшно": 0.7, "жутко": 0.8, "пугает": 0.6
            },
            
            EmotionType.SURPRISE: {
                # Сильное удивление
                "шок": 0.9, "потрясение": 0.9, "ошеломление": 0.9,
                "изумление": 0.8, "поражение": 0.8,
                # Умеренное удивление
                "удивление": 0.7, "удивлён": 0.7, "поразительно": 0.8,
                "неожиданно": 0.6, "внезапно": 0.6, "вдруг": 0.5,
                # Слабое удивление
                "интересно": 0.4, "любопытно": 0.4, "странно": 0.5,
                "необычно": 0.5, "удивительно": 0.6,
                # Выражения удивления
                "ого": 0.6, "ух ты": 0.7, "вау": 0.7, "офигеть": 0.8,
                "не может быть": 0.8, "невероятно": 0.8
            },
            
            EmotionType.DISGUST: {
                # Сильное отвращение
                "отвращение": 0.9, "омерзение": 0.9, "тошнота": 0.8,
                "мерзость": 0.8, "гадость": 0.7, "противность": 0.7,
                # Умеренное отвращение
                "неприязнь": 0.6, "антипатия": 0.6, "брезгливость": 0.7,
                "отталкивает": 0.6, "противно": 0.7, "мерзко": 0.8,
                # Слабое отвращение
                "не нравится": 0.4, "плохо": 0.3, "неприятно": 0.4,
                "фу": 0.6, "бе": 0.5, "фигня": 0.5
            },
            
            EmotionType.TRUST: {
                # Сильное доверие
                "доверие": 0.8, "вера": 0.7, "уверенность": 0.7,
                "надежность": 0.8, "верность": 0.8, "преданность": 0.8,
                # Умеренное доверие
                "доверяю": 0.7, "верю": 0.7, "полагаюсь": 0.6,
                "рассчитываю": 0.5, "надеюсь": 0.5, "ожидаю": 0.4,
                # Слабое доверие
                "возможно": 0.3, "наверное": 0.3, "думаю": 0.3,
                "считаю": 0.4, "полагаю": 0.4
            },
            
            EmotionType.ANTICIPATION: {
                # Сильное предвкушение
                "предвкушение": 0.8, "ожидание": 0.7, "нетерпение": 0.8,
                "жажда": 0.7, "стремление": 0.6, "желание": 0.6,
                # Умеренное предвкушение
                "хочется": 0.6, "хочу": 0.6, "жду": 0.5,
                "планирую": 0.4, "собираюсь": 0.4, "намереваюсь": 0.4,
                # Слабое предвкушение
                "интерес": 0.4, "любопытство": 0.4, "заинтересован": 0.5,
                "готов": 0.5, "готова": 0.5
            }
        }
    
    def _init_intensity_modifiers(self) -> Dict[str, float]:
        """Инициализация модификаторов интенсивности"""
        return {
            # Усилители
            "очень": 1.5, "крайне": 1.8, "чрезвычайно": 2.0, "невероятно": 1.9,
            "супер": 1.6, "мега": 1.7, "ультра": 1.8, "гипер": 1.9,
            "безумно": 1.8, "дико": 1.7, "жутко": 1.6, "страшно": 1.5,
            "ужасно": 1.7, "кошмарно": 1.8, "адски": 1.9, "пиздец": 2.0,
            
            # Ослабители
            "немного": 0.6, "слегка": 0.5, "чуть": 0.4, "едва": 0.3,
            "почти": 0.7, "практически": 0.8, "довольно": 0.8,
            "относительно": 0.7, "сравнительно": 0.7, "несколько": 0.6,
            
            # Нейтральные
            "просто": 1.0, "обычно": 1.0, "нормально": 1.0
        }
    
    def analyze_emotion(self, text: str, context: Optional[str] = None) -> Dict[str, any]:
        """
        Основной метод анализа эмоций в тексте
        
        Args:
            text: Текст для анализа
            context: Дополнительный контекст (опционально)
            
        Returns:
            Dict с результатами анализа эмоций
        """
        try:
            text_lower = text.lower()
            
            # 1. Базовый анализ эмоций
            emotion_scores = self._calculate_emotion_scores(text_lower)
            
            # 2. Применение модификаторов интенсивности
            emotion_scores = self._apply_intensity_modifiers(text_lower, emotion_scores)
            
            # 3. Обработка отрицаний
            emotion_scores = self._handle_negations(text_lower, emotion_scores)
            
            # 4. Нормализация и определение доминирующей эмоции
            normalized_scores = self._normalize_scores(emotion_scores)
            dominant_emotion, confidence = self._get_dominant_emotion(normalized_scores)
            
            # 5. Расчет валентности и возбуждения
            valence = self._calculate_valence(normalized_scores)
            arousal = self._calculate_arousal(normalized_scores)
            
            # 6. Определение интенсивности
            intensity_level = self._determine_intensity_level(confidence)
            
            # 7. Контекстный анализ (если есть контекст)
            if context:
                context_adjustment = self._analyze_context(context, dominant_emotion)
                confidence *= context_adjustment
            
            # 8. Обновление истории эмоций
            self._update_emotion_history(dominant_emotion, confidence)
            
            result = {
                "dominant_emotion": dominant_emotion,
                "confidence": confidence,
                "intensity": intensity_level,
                "valence": valence,
                "arousal": arousal,
                "all_emotions": normalized_scores,
                "raw_scores": emotion_scores,
                "analysis_timestamp": datetime.now(),
                "text_length": len(text),
                "emotional_complexity": len([e for e in normalized_scores.values() if e > 0.1])
            }
            
            logger.debug(f"Emotion analysis result: {dominant_emotion} ({confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in emotion analysis: {e}")
            return self._get_default_analysis()
    
    def _calculate_emotion_scores(self, text: str) -> Dict[EmotionType, float]:
        """Базовый расчет оценок эмоций"""
        emotion_scores = {emotion: 0.0 for emotion in EmotionType}
        
        words = re.findall(r'\b\w+\b', text)
        
        for emotion_type, lexicon in self.emotion_lexicons.items():
            total_score = 0.0
            word_count = 0
            
            for word in words:
                if word in lexicon:
                    total_score += lexicon[word]
                    word_count += 1
            
            if word_count > 0:
                # Нормализуем по количеству найденных слов
                emotion_scores[emotion_type] = total_score / len(words)
        
        return emotion_scores
    
    def _apply_intensity_modifiers(self, text: str, scores: Dict[EmotionType, float]) -> Dict[EmotionType, float]:
        """Применение модификаторов интенсивности"""
        words = text.split()
        modified_scores = scores.copy()
        
        for i, word in enumerate(words):
            if word in self.intensity_modifiers:
                modifier = self.intensity_modifiers[word]
                
                # Применяем модификатор к следующим 2-3 словам
                for j in range(i+1, min(i+4, len(words))):
                    next_word = words[j]
                    
                    # Ищем эмоциональные слова для модификации
                    for emotion_type, lexicon in self.emotion_lexicons.items():
                        if next_word in lexicon:
                            original_weight = lexicon[next_word] / len(words)
                            modified_scores[emotion_type] += original_weight * (modifier - 1.0)
                            break
        
        return modified_scores
    
    def _handle_negations(self, text: str, scores: Dict[EmotionType, float]) -> Dict[EmotionType, float]:
        """Обработка отрицаний"""
        words = text.split()
        modified_scores = scores.copy()
        
        for i, word in enumerate(words):
            if word in self.negation_words:
                # Инвертируем эмоции в следующих 3-4 словах
                for j in range(i+1, min(i+5, len(words))):
                    next_word = words[j]
                    
                    for emotion_type, lexicon in self.emotion_lexicons.items():
                        if next_word in lexicon:
                            # Уменьшаем положительные эмоции, увеличиваем отрицательные
                            if emotion_type in [EmotionType.JOY, EmotionType.TRUST, EmotionType.ANTICIPATION]:
                                modified_scores[emotion_type] *= 0.3
                            elif emotion_type in [EmotionType.SADNESS, EmotionType.ANGER, EmotionType.FEAR, EmotionType.DISGUST]:
                                modified_scores[emotion_type] *= 1.5
        
        return modified_scores
    
    def _normalize_scores(self, scores: Dict[EmotionType, float]) -> Dict[EmotionType, float]:
        """Нормализация оценок эмоций"""
        max_score = max(scores.values()) if scores.values() else 1.0
        
        if max_score > 0:
            return {emotion: score / max_score for emotion, score in scores.items()}
        else:
            return {emotion: 0.0 for emotion in scores.keys()}
    
    def _get_dominant_emotion(self, scores: Dict[EmotionType, float]) -> Tuple[EmotionType, float]:
        """Определение доминирующей эмоции"""
        if not scores:
            return EmotionType.NEUTRAL, 0.0
        
        max_emotion = max(scores.items(), key=lambda x: x[1])
        
        # Если оценка слишком низкая, считаем эмоцию нейтральной
        if max_emotion[1] < 0.1:
            return EmotionType.NEUTRAL, 0.0
        
        return max_emotion[0], max_emotion[1]
    
    def _calculate_valence(self, scores: Dict[EmotionType, float]) -> float:
        """Расчет валентности (позитивность/негативность)"""
        positive_emotions = [EmotionType.JOY, EmotionType.TRUST, EmotionType.ANTICIPATION]
        negative_emotions = [EmotionType.SADNESS, EmotionType.ANGER, EmotionType.FEAR, EmotionType.DISGUST]
        
        positive_score = sum(scores.get(emotion, 0) for emotion in positive_emotions)
        negative_score = sum(scores.get(emotion, 0) for emotion in negative_emotions)
        
        if positive_score + negative_score == 0:
            return 0.0
        
        return (positive_score - negative_score) / (positive_score + negative_score)
    
    def _calculate_arousal(self, scores: Dict[EmotionType, float]) -> float:
        """Расчет уровня возбуждения/активации"""
        high_arousal_emotions = [EmotionType.ANGER, EmotionType.FEAR, EmotionType.JOY, EmotionType.SURPRISE]
        low_arousal_emotions = [EmotionType.SADNESS, EmotionType.TRUST]
        
        high_arousal_score = sum(scores.get(emotion, 0) for emotion in high_arousal_emotions)
        low_arousal_score = sum(scores.get(emotion, 0) for emotion in low_arousal_emotions)
        
        total_score = high_arousal_score + low_arousal_score
        
        if total_score == 0:
            return 0.5  # Нейтральный уровень возбуждения
        
        return high_arousal_score / total_score
    
    def _determine_intensity_level(self, confidence: float) -> EmotionIntensity:
        """Определение уровня интенсивности эмоции"""
        if confidence >= 0.8:
            return EmotionIntensity.VERY_HIGH
        elif confidence >= 0.6:
            return EmotionIntensity.HIGH
        elif confidence >= 0.4:
            return EmotionIntensity.MEDIUM
        elif confidence >= 0.2:
            return EmotionIntensity.LOW
        else:
            return EmotionIntensity.VERY_LOW
    
    def _analyze_context(self, context: str, emotion: EmotionType) -> float:
        """Контекстный анализ эмоций"""
        # Простая реализация - можно расширить
        context_analysis = self.analyze_emotion(context)
        context_emotion = context_analysis["dominant_emotion"]
        
        # Если эмоции совпадают, увеличиваем уверенность
        if context_emotion == emotion:
            return 1.2
        # Если эмоции противоположны, уменьшаем уверенность
        elif self._are_opposite_emotions(emotion, context_emotion):
            return 0.8
        else:
            return 1.0
    
    def _are_opposite_emotions(self, emotion1: EmotionType, emotion2: EmotionType) -> bool:
        """Проверка на противоположные эмоции"""
        opposite_pairs = [
            (EmotionType.JOY, EmotionType.SADNESS),
            (EmotionType.ANGER, EmotionType.TRUST),
            (EmotionType.FEAR, EmotionType.ANTICIPATION),
            (EmotionType.SURPRISE, EmotionType.NEUTRAL)
        ]
        
        return any((emotion1, emotion2) in pair or (emotion2, emotion1) in pair for pair in opposite_pairs)
    
    def _update_emotion_history(self, emotion: EmotionType, confidence: float):
        """Обновление истории эмоций"""
        self.emotion_history.append((datetime.now(), emotion, confidence))
        
        # Ограничиваем размер истории
        if len(self.emotion_history) > self.max_history_size:
            self.emotion_history = self.emotion_history[-self.max_history_size:]
    
    def _get_default_analysis(self) -> Dict[str, any]:
        """Результат анализа по умолчанию при ошибке"""
        return {
            "dominant_emotion": EmotionType.NEUTRAL,
            "confidence": 0.0,
            "intensity": EmotionIntensity.VERY_LOW,
            "valence": 0.0,
            "arousal": 0.5,
            "all_emotions": {emotion: 0.0 for emotion in EmotionType},
            "raw_scores": {emotion: 0.0 for emotion in EmotionType},
            "analysis_timestamp": datetime.now(),
            "text_length": 0,
            "emotional_complexity": 0
        }
    
    def get_emotion_trends(self, hours: int = 24) -> Dict[str, any]:
        """Получение трендов эмоций за указанный период"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_emotions = [
            (timestamp, emotion, confidence) 
            for timestamp, emotion, confidence in self.emotion_history 
            if timestamp >= cutoff_time
        ]
        
        if not recent_emotions:
            return {"trend": "neutral", "dominant_emotions": [], "average_confidence": 0.0}
        
        # Подсчет частоты эмоций
        emotion_counts = {}
        total_confidence = 0.0
        
        for _, emotion, confidence in recent_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_confidence += confidence
        
        # Определение доминирующих эмоций
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "trend": sorted_emotions[0][0] if sorted_emotions else EmotionType.NEUTRAL,
            "dominant_emotions": sorted_emotions[:3],
            "average_confidence": total_confidence / len(recent_emotions),
            "total_analyses": len(recent_emotions),
            "time_period_hours": hours
        }
