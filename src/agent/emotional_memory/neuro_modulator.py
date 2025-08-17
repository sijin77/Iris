"""
Нейромодулятор для эмоциональной памяти.
Имитирует работу нейротрансмиттеров для модуляции важности и приоритета воспоминаний.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from .models import ModulatorType, EmotionalFragment, EmotionType
from ..memory.models import MemoryFragment

logger = logging.getLogger(__name__)


class ModulationEffect(str, Enum):
    """Эффекты нейромодуляции"""
    ENHANCEMENT = "enhancement"    # Усиление
    SUPPRESSION = "suppression"    # Подавление
    STABILIZATION = "stabilization"  # Стабилизация
    FACILITATION = "facilitation"  # Облегчение


class NeuroModulator:
    """
    Нейромодулятор для эмоциональной памяти.
    
    Имитирует работу различных нейротрансмиттеров:
    - Дофамин: вознаграждение, мотивация, обучение
    - Серотонин: настроение, удовлетворенность, стабильность
    - Норэпинефрин: внимание, стресс, активация
    - Ацетилхолин: обучение, память, внимание
    - ГАМК: торможение, расслабление, стабилизация
    """
    
    def __init__(self):
        # Базовые уровни нейромодуляторов (0.0-1.0)
        self.base_levels = {
            ModulatorType.DOPAMINE: 0.5,
            ModulatorType.SEROTONIN: 0.6,
            ModulatorType.NOREPINEPHRINE: 0.4,
            ModulatorType.ACETYLCHOLINE: 0.5,
            ModulatorType.GABA: 0.6
        }
        
        # Текущие уровни (могут изменяться)
        self.current_levels = self.base_levels.copy()
        
        # История изменений уровней
        self.level_history: List[Tuple[datetime, Dict[ModulatorType, float]]] = []
        
        # Конфигурация эффектов
        self.modulation_effects = self._init_modulation_effects()
        
        # Пороги для активации
        self.activation_thresholds = {
            ModulatorType.DOPAMINE: 0.7,      # Высокий порог для награды
            ModulatorType.SEROTONIN: 0.3,     # Низкий порог для стабилизации
            ModulatorType.NOREPINEPHRINE: 0.6, # Средний порог для стресса
            ModulatorType.ACETYLCHOLINE: 0.5,  # Средний порог для обучения
            ModulatorType.GABA: 0.4           # Низкий порог для торможения
        }
        
        # Время полураспада (как долго действует модуляция)
        self.half_life_minutes = {
            ModulatorType.DOPAMINE: 30,       # Быстрое действие
            ModulatorType.SEROTONIN: 120,     # Длительное действие
            ModulatorType.NOREPINEPHRINE: 15, # Очень быстрое действие
            ModulatorType.ACETYLCHOLINE: 45,  # Умеренное действие
            ModulatorType.GABA: 60            # Умеренное действие
        }
    
    def _init_modulation_effects(self) -> Dict[ModulatorType, Dict[str, float]]:
        """Инициализация эффектов нейромодуляции"""
        return {
            ModulatorType.DOPAMINE: {
                "priority_multiplier": 1.5,    # Увеличивает приоритет
                "learning_rate": 1.3,          # Улучшает обучение
                "motivation_boost": 1.4,       # Повышает мотивацию
                "reward_sensitivity": 1.6,     # Увеличивает чувствительность к награде
                "memory_consolidation": 1.2    # Улучшает консолидацию памяти
            },
            
            ModulatorType.SEROTONIN: {
                "mood_stabilization": 1.0,     # Стабилизирует настроение
                "anxiety_reduction": 0.7,      # Снижает тревожность
                "impulse_control": 1.2,        # Улучшает контроль импульсов
                "social_processing": 1.3,      # Улучшает социальную обработку
                "emotional_regulation": 1.4    # Улучшает эмоциональную регуляцию
            },
            
            ModulatorType.NOREPINEPHRINE: {
                "attention_focus": 1.6,        # Улучшает фокус внимания
                "stress_response": 1.8,        # Усиливает стрессовую реакцию
                "memory_encoding": 1.4,        # Улучшает кодирование памяти
                "arousal_level": 1.5,          # Повышает уровень возбуждения
                "alertness": 1.7               # Повышает бдительность
            },
            
            ModulatorType.ACETYLCHOLINE: {
                "learning_enhancement": 1.5,   # Улучшает обучение
                "attention_switching": 1.3,    # Улучшает переключение внимания
                "memory_retrieval": 1.4,       # Улучшает извлечение памяти
                "cognitive_flexibility": 1.2,  # Повышает когнитивную гибкость
                "pattern_recognition": 1.3     # Улучшает распознавание паттернов
            },
            
            ModulatorType.GABA: {
                "anxiety_reduction": 0.5,      # Сильно снижает тревожность
                "inhibition_control": 1.3,     # Улучшает контроль торможения
                "relaxation": 0.6,             # Способствует расслаблению
                "sleep_quality": 1.2,          # Улучшает качество сна
                "emotional_dampening": 0.8     # Смягчает эмоциональные реакции
            }
        }
    
    def modulate_fragment(self, fragment: MemoryFragment, emotion_analysis: Dict) -> MemoryFragment:
        """
        Применяет нейромодуляцию к фрагменту памяти
        
        Args:
            fragment: Фрагмент памяти для модуляции
            emotion_analysis: Результат анализа эмоций
            
        Returns:
            Модулированный фрагмент памяти
        """
        try:
            # Определяем, какие нейромодуляторы должны быть активированы
            active_modulators = self._determine_active_modulators(emotion_analysis)
            
            # Создаем копию фрагмента для модификации
            modulated_fragment = fragment.copy(deep=True)
            
            # Применяем каждый активный модулятор
            for modulator_type, activation_level in active_modulators.items():
                modulated_fragment = self._apply_modulator_effects(
                    modulated_fragment, modulator_type, activation_level, emotion_analysis
                )
            
            # Обновляем метаданные с информацией о модуляции
            if not hasattr(modulated_fragment, 'metadata'):
                modulated_fragment.metadata = {}
            
            modulated_fragment.metadata.update({
                "neuro_modulation": {
                    "active_modulators": {k.value: v for k, v in active_modulators.items()},
                    "modulation_timestamp": datetime.now().isoformat(),
                    "original_priority": fragment.priority,
                    "modulation_applied": True
                }
            })
            
            # Записываем в историю
            self._record_modulation_event(active_modulators, emotion_analysis)
            
            logger.debug(f"Applied neuro-modulation to fragment {fragment.id}: {list(active_modulators.keys())}")
            
            return modulated_fragment
            
        except Exception as e:
            logger.error(f"Error in neuro-modulation: {e}")
            return fragment
    
    def _determine_active_modulators(self, emotion_analysis: Dict) -> Dict[ModulatorType, float]:
        """Определяет, какие нейромодуляторы должны быть активированы"""
        active_modulators = {}
        
        dominant_emotion = emotion_analysis.get("dominant_emotion", EmotionType.NEUTRAL)
        confidence = emotion_analysis.get("confidence", 0.0)
        valence = emotion_analysis.get("valence", 0.0)
        arousal = emotion_analysis.get("arousal", 0.5)
        
        # Дофамин активируется при положительных эмоциях и высокой уверенности
        if valence > 0.3 and confidence > 0.6:
            dopamine_level = min(1.0, (valence + confidence) / 2.0)
            if dopamine_level > self.activation_thresholds[ModulatorType.DOPAMINE]:
                active_modulators[ModulatorType.DOPAMINE] = dopamine_level
        
        # Серотонин активируется для стабилизации настроения
        if dominant_emotion in [EmotionType.JOY, EmotionType.TRUST] or abs(valence) < 0.3:
            serotonin_level = max(0.3, 1.0 - abs(valence))
            active_modulators[ModulatorType.SEROTONIN] = serotonin_level
        
        # Норэпинефрин активируется при стрессе, страхе, гневе
        if dominant_emotion in [EmotionType.FEAR, EmotionType.ANGER] or arousal > 0.7:
            norepinephrine_level = max(arousal, confidence if dominant_emotion in [EmotionType.FEAR, EmotionType.ANGER] else 0)
            if norepinephrine_level > self.activation_thresholds[ModulatorType.NOREPINEPHRINE]:
                active_modulators[ModulatorType.NOREPINEPHRINE] = norepinephrine_level
        
        # Ацетилхолин активируется при обучении и внимании
        if dominant_emotion in [EmotionType.SURPRISE, EmotionType.ANTICIPATION] or confidence > 0.7:
            acetylcholine_level = max(confidence, arousal if dominant_emotion == EmotionType.SURPRISE else 0.5)
            if acetylcholine_level > self.activation_thresholds[ModulatorType.ACETYLCHOLINE]:
                active_modulators[ModulatorType.ACETYLCHOLINE] = acetylcholine_level
        
        # ГАМК активируется при необходимости торможения
        if arousal > 0.8 or dominant_emotion == EmotionType.ANGER:
            gaba_level = min(1.0, arousal * 0.8)  # Обратная зависимость от возбуждения
            if gaba_level > self.activation_thresholds[ModulatorType.GABA]:
                active_modulators[ModulatorType.GABA] = gaba_level
        
        return active_modulators
    
    def _apply_modulator_effects(self, fragment: MemoryFragment, modulator_type: ModulatorType, 
                                activation_level: float, emotion_analysis: Dict) -> MemoryFragment:
        """Применяет эффекты конкретного нейромодулятора"""
        
        effects = self.modulation_effects[modulator_type]
        
        if modulator_type == ModulatorType.DOPAMINE:
            # Дофамин усиливает приоритет и способствует обучению
            fragment.priority *= (1.0 + (activation_level * (effects["priority_multiplier"] - 1.0)))
            fragment.priority = min(1.0, fragment.priority)  # Ограничиваем максимум
            
            # Добавляем "награду" в метаданные
            if not hasattr(fragment, 'metadata'):
                fragment.metadata = {}
            fragment.metadata["dopamine_reward"] = activation_level
            
        elif modulator_type == ModulatorType.SEROTONIN:
            # Серотонин стабилизирует и улучшает эмоциональную регуляцию
            # Сглаживает экстремальные приоритеты
            if fragment.priority > 0.8:
                fragment.priority *= effects["emotional_regulation"]
            elif fragment.priority < 0.2:
                fragment.priority = max(0.2, fragment.priority * effects["mood_stabilization"])
                
        elif modulator_type == ModulatorType.NOREPINEPHRINE:
            # Норэпинефрин усиливает внимание к стрессовым событиям
            if emotion_analysis.get("dominant_emotion") in [EmotionType.FEAR, EmotionType.ANGER]:
                fragment.priority *= effects["attention_focus"] * activation_level
                fragment.priority = min(1.0, fragment.priority)
                
            # Улучшает кодирование памяти при стрессе
            if not hasattr(fragment, 'metadata'):
                fragment.metadata = {}
            fragment.metadata["stress_enhanced"] = activation_level > 0.7
            
        elif modulator_type == ModulatorType.ACETYLCHOLINE:
            # Ацетилхолин улучшает обучение и внимание
            learning_bonus = effects["learning_enhancement"] * activation_level
            fragment.priority *= (1.0 + (learning_bonus - 1.0) * 0.5)  # Умеренное усиление
            
            # Помечаем как важное для обучения
            if not hasattr(fragment, 'metadata'):
                fragment.metadata = {}
            fragment.metadata["learning_relevant"] = True
            fragment.metadata["attention_enhanced"] = activation_level
            
        elif modulator_type == ModulatorType.GABA:
            # ГАМК подавляет чрезмерную активацию
            if fragment.priority > 0.7:
                fragment.priority *= effects["emotional_dampening"]
            
            # Способствует "забыванию" менее важных деталей
            if fragment.priority < 0.3:
                fragment.priority *= effects["relaxation"]
        
        return fragment
    
    def apply_dopamine_reward(self, fragment: MemoryFragment, reward_strength: float) -> MemoryFragment:
        """
        Применяет дофаминовое подкрепление к фрагменту памяти
        (аналог функции из HEAPmemory.py)
        
        Args:
            fragment: Фрагмент памяти
            reward_strength: Сила награды (0.0-1.0)
            
        Returns:
            Модулированный фрагмент
        """
        try:
            modulated_fragment = fragment.copy(deep=True)
            
            # Увеличиваем приоритет на основе силы награды
            dopamine_multiplier = 1.0 + (reward_strength * 0.5)  # Максимум +50%
            modulated_fragment.priority *= dopamine_multiplier
            modulated_fragment.priority = min(1.0, modulated_fragment.priority)
            
            # Обновляем уровень дофамина
            self.current_levels[ModulatorType.DOPAMINE] = min(1.0, 
                self.current_levels[ModulatorType.DOPAMINE] + reward_strength * 0.3
            )
            
            # Добавляем метаданные
            if not hasattr(modulated_fragment, 'metadata'):
                modulated_fragment.metadata = {}
            
            modulated_fragment.metadata.update({
                "neuro_modulator": "dopamine",
                "reward_strength": reward_strength,
                "dopamine_applied": datetime.now().isoformat(),
                "priority_boost": dopamine_multiplier
            })
            
            logger.debug(f"Applied dopamine reward {reward_strength} to fragment {fragment.id}")
            
            return modulated_fragment
            
        except Exception as e:
            logger.error(f"Error applying dopamine reward: {e}")
            return fragment
    
    def decay_modulators(self, minutes_elapsed: int):
        """Применяет естественный распад нейромодуляторов"""
        for modulator_type, half_life in self.half_life_minutes.items():
            decay_factor = 0.5 ** (minutes_elapsed / half_life)
            
            # Возвращаем уровень к базовому с учетом распада
            current = self.current_levels[modulator_type]
            base = self.base_levels[modulator_type]
            
            self.current_levels[modulator_type] = base + (current - base) * decay_factor
    
    def _record_modulation_event(self, active_modulators: Dict[ModulatorType, float], emotion_analysis: Dict):
        """Записывает событие модуляции в историю"""
        # Обновляем текущие уровни
        for modulator_type, activation_level in active_modulators.items():
            self.current_levels[modulator_type] = min(1.0, 
                self.current_levels[modulator_type] + activation_level * 0.2
            )
        
        # Записываем в историю
        self.level_history.append((datetime.now(), self.current_levels.copy()))
        
        # Ограничиваем размер истории
        if len(self.level_history) > 100:
            self.level_history = self.level_history[-100:]
    
    def get_current_state(self) -> Dict:
        """Получает текущее состояние нейромодуляторов"""
        return {
            "current_levels": self.current_levels.copy(),
            "base_levels": self.base_levels.copy(),
            "activation_thresholds": self.activation_thresholds.copy(),
            "last_update": datetime.now().isoformat(),
            "history_length": len(self.level_history)
        }
    
    def get_modulation_history(self, hours: int = 24) -> List[Dict]:
        """Получает историю модуляции за указанный период"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_history = [
            {
                "timestamp": timestamp.isoformat(),
                "levels": levels
            }
            for timestamp, levels in self.level_history
            if timestamp >= cutoff_time
        ]
        
        return recent_history
    
    def reset_to_baseline(self):
        """Сбрасывает все уровни к базовым значениям"""
        self.current_levels = self.base_levels.copy()
        logger.info("Neuro-modulator levels reset to baseline")
    
    def adjust_baseline(self, modulator_type: ModulatorType, new_baseline: float):
        """Корректирует базовый уровень нейромодулятора"""
        if 0.0 <= new_baseline <= 1.0:
            self.base_levels[modulator_type] = new_baseline
            logger.info(f"Baseline for {modulator_type} adjusted to {new_baseline}")
        else:
            logger.warning(f"Invalid baseline value {new_baseline} for {modulator_type}")
    
    def simulate_drug_effect(self, modulator_type: ModulatorType, effect_strength: float, duration_minutes: int):
        """
        Симулирует эффект "препарата" на нейромодулятор
        (для тестирования и исследований)
        """
        original_level = self.current_levels[modulator_type]
        
        # Применяем эффект
        self.current_levels[modulator_type] = min(1.0, 
            original_level + effect_strength
        )
        
        # Записываем событие
        self.level_history.append((datetime.now(), self.current_levels.copy()))
        
        logger.info(f"Simulated {modulator_type} effect: {effect_strength} for {duration_minutes} minutes")
