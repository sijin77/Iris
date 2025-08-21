#!/usr/bin/env python3
"""
Миграция для добавления настроек эмоциональной памяти и нейромодуляции
в таблицу agent_summarization_settings.

Добавляет колонки:
- emotion_triggers: триггеры эмоций с весами
- neuromodulator_settings: настройки нейромодуляторов
- emotion_analysis_config: конфигурация анализа эмоций
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
from config.database import DATABASE_URL
import logging
import json

logger = logging.getLogger(__name__)


def get_comprehensive_emotion_triggers() -> dict:
    """Возвращает полный набор эмоциональных триггеров с весами"""
    return {
        "joy_triggers": {
            # Сильная радость (вес 0.8-1.0)
            "восторг": 0.9, "счастье": 0.9, "блаженство": 0.9, "эйфория": 1.0,
            "ликование": 0.9, "экстаз": 1.0, "упоение": 0.8,
            "потрясающе": 0.9, "шикарно": 0.8, "божественно": 0.9,
            
            # Умеренная радость (вес 0.5-0.7)
            "радость": 0.8, "веселье": 0.7, "довольство": 0.6, "удовлетворение": 0.6,
            "приятно": 0.6, "хорошо": 0.5, "отлично": 0.8, "прекрасно": 0.8,
            "замечательно": 0.8, "великолепно": 0.9, "чудесно": 0.8,
            "супер": 0.8, "класс": 0.7, "круто": 0.7, "офигенно": 0.8,
            
            # Слабая радость (вес 0.3-0.5)
            "улыбка": 0.4, "смех": 0.6, "смешно": 0.5, "забавно": 0.5,
            "нравится": 0.6, "люблю": 0.7, "обожаю": 0.8, "кайф": 0.7,
            
            # English equivalents
            "awesome": 0.9, "fantastic": 0.9, "amazing": 0.9, "wonderful": 0.8,
            "great": 0.7, "good": 0.5, "nice": 0.5, "cool": 0.6, "love": 0.7
        },
        
        "sadness_triggers": {
            # Сильная грусть (вес 0.8-1.0)
            "горе": 0.9, "скорбь": 0.9, "отчаяние": 1.0, "депрессия": 0.9,
            "тоска": 0.8, "печаль": 0.8, "уныние": 0.7, "меланхолия": 0.7,
            
            # Умеренная грусть (вес 0.5-0.7)
            "грусть": 0.7, "грустно": 0.7, "расстройство": 0.6, "огорчение": 0.6,
            "разочарование": 0.7, "сожаление": 0.6, "жалость": 0.5,
            "слёзы": 0.7, "плач": 0.8, "рыдания": 0.9,
            
            # Слабая грусть (вес 0.3-0.5)
            "плохо": 0.5, "неприятно": 0.5, "досадно": 0.4, "жаль": 0.5,
            "потеря": 0.7, "утрата": 0.8, "лишение": 0.6, "разлука": 0.7,
            
            # English equivalents
            "sad": 0.7, "depressed": 0.9, "upset": 0.6, "disappointed": 0.7,
            "sorry": 0.5, "regret": 0.6, "loss": 0.7, "grief": 0.9
        },
        
        "anger_triggers": {
            # Сильная злость (вес 0.8-1.0)
            "ярость": 1.0, "бешенство": 1.0, "гнев": 0.9, "неистовство": 1.0,
            "остервенение": 1.0, "исступление": 1.0,
            
            # Умеренная злость (вес 0.5-0.7)
            "злость": 0.8, "злой": 0.8, "раздражение": 0.6, "досада": 0.5,
            "недовольство": 0.5, "возмущение": 0.7, "негодование": 0.7,
            "агрессия": 0.8, "враждебность": 0.7, "ненависть": 0.9,
            "отвращение": 0.7, "презрение": 0.6,
            
            # Выражения злости (вес 0.4-0.8)
            "бесит": 0.8, "раздражает": 0.6, "злюсь": 0.8, "взбешён": 0.9,
            "сердитый": 0.6, "рассерженный": 0.7, "взбешенный": 0.9,
            "чёрт": 0.6, "блин": 0.4, "капец": 0.7, "ужас": 0.6,
            
            # English equivalents
            "angry": 0.8, "mad": 0.8, "furious": 1.0, "rage": 1.0,
            "irritated": 0.6, "annoyed": 0.5, "pissed": 0.8, "hate": 0.9
        },
        
        "fear_triggers": {
            # Сильный страх (вес 0.8-1.0)
            "ужас": 1.0, "кошмар": 0.9, "паника": 1.0, "террор": 1.0,
            "испуг": 0.7, "шок": 0.8, "оцепенение": 0.8,
            
            # Умеренный страх (вес 0.5-0.7)
            "страх": 0.8, "боязнь": 0.7, "опасение": 0.5, "тревога": 0.6,
            "беспокойство": 0.5, "волнение": 0.4, "нервозность": 0.6,
            
            # Слабый страх (вес 0.3-0.5)
            "переживание": 0.4, "сомнение": 0.3, "неуверенность": 0.4,
            "боюсь": 0.7, "страшно": 0.7, "жутко": 0.8, "пугает": 0.6,
            
            # English equivalents
            "fear": 0.8, "scared": 0.7, "afraid": 0.7, "terrified": 1.0,
            "panic": 1.0, "worried": 0.5, "nervous": 0.6, "anxious": 0.6
        },
        
        "surprise_triggers": {
            # Сильное удивление (вес 0.8-1.0)
            "шок": 0.9, "потрясение": 0.9, "ошеломление": 0.9,
            "изумление": 0.8, "поражение": 0.8,
            
            # Умеренное удивление (вес 0.5-0.7)
            "удивление": 0.7, "удивлён": 0.7, "поразительно": 0.8,
            "неожиданно": 0.6, "внезапно": 0.6, "вдруг": 0.5,
            
            # Слабое удивление (вес 0.3-0.5)
            "интересно": 0.4, "любопытно": 0.4, "странно": 0.5,
            "необычно": 0.5, "удивительно": 0.6,
            
            # Выражения удивления (вес 0.6-0.8)
            "ого": 0.6, "ух ты": 0.7, "вау": 0.7, "офигеть": 0.8,
            "не может быть": 0.8, "невероятно": 0.8,
            
            # English equivalents
            "wow": 0.7, "amazing": 0.8, "incredible": 0.8, "unbelievable": 0.8,
            "surprised": 0.7, "shocked": 0.9, "astonished": 0.8
        },
        
        "disgust_triggers": {
            # Сильное отвращение (вес 0.7-0.9)
            "отвращение": 0.9, "омерзение": 0.9, "тошнота": 0.8,
            "мерзость": 0.8, "гадость": 0.7, "противность": 0.7,
            
            # Умеренное отвращение (вес 0.5-0.7)
            "неприязнь": 0.6, "антипатия": 0.6, "брезгливость": 0.7,
            "отталкивает": 0.6, "противно": 0.7, "мерзко": 0.8,
            
            # Слабое отвращение (вес 0.3-0.5)
            "не нравится": 0.4, "плохо": 0.3, "неприятно": 0.4,
            "фу": 0.6, "бе": 0.5, "фигня": 0.5,
            
            # English equivalents
            "disgusting": 0.8, "gross": 0.7, "yuck": 0.6, "hate": 0.7,
            "awful": 0.6, "terrible": 0.6, "horrible": 0.7
        },
        
        "trust_triggers": {
            # Сильное доверие (вес 0.7-0.8)
            "доверие": 0.8, "вера": 0.7, "уверенность": 0.7,
            "надежность": 0.8, "верность": 0.8, "преданность": 0.8,
            
            # Умеренное доверие (вес 0.5-0.7)
            "доверяю": 0.7, "верю": 0.7, "полагаюсь": 0.6,
            "рассчитываю": 0.5, "надеюсь": 0.5, "ожидаю": 0.4,
            
            # Слабое доверие (вес 0.3-0.5)
            "возможно": 0.3, "наверное": 0.3, "думаю": 0.3,
            "считаю": 0.4, "полагаю": 0.4,
            
            # English equivalents
            "trust": 0.8, "believe": 0.7, "confident": 0.7, "reliable": 0.8,
            "faith": 0.7, "hope": 0.5, "expect": 0.4
        },
        
        "anticipation_triggers": {
            # Сильное предвкушение (вес 0.6-0.8)
            "предвкушение": 0.8, "ожидание": 0.7, "нетерпение": 0.8,
            "жажда": 0.7, "стремление": 0.6, "желание": 0.6,
            
            # Умеренное предвкушение (вес 0.4-0.6)
            "хочется": 0.6, "хочу": 0.6, "жду": 0.5,
            "планирую": 0.4, "собираюсь": 0.4, "намереваюсь": 0.4,
            
            # Слабое предвкушение (вес 0.3-0.5)
            "интерес": 0.4, "любопытство": 0.4, "заинтересован": 0.5,
            "готов": 0.5, "готова": 0.5,
            
            # English equivalents
            "anticipation": 0.8, "expectation": 0.7, "excitement": 0.7,
            "want": 0.6, "desire": 0.6, "looking forward": 0.7
        }
    }


def get_comprehensive_neuromodulator_settings() -> dict:
    """Возвращает полные настройки нейромодуляторов"""
    return {
        "base_levels": {
            "dopamine": 0.5,
            "serotonin": 0.6,
            "norepinephrine": 0.4,
            "acetylcholine": 0.5,
            "gaba": 0.6
        },
        
        "activation_thresholds": {
            "dopamine": 0.7,      # Высокий порог для награды
            "serotonin": 0.3,     # Низкий порог для стабилизации
            "norepinephrine": 0.6, # Средний порог для стресса
            "acetylcholine": 0.5,  # Средний порог для обучения
            "gaba": 0.4           # Низкий порог для торможения
        },
        
        "half_life_minutes": {
            "dopamine": 30,       # Быстрое действие
            "serotonin": 120,     # Длительное действие
            "norepinephrine": 15, # Очень быстрое действие
            "acetylcholine": 45,  # Умеренное действие
            "gaba": 60            # Умеренное действие
        },
        
        "modulation_effects": {
            "dopamine": {
                "priority_multiplier": 1.5,    # Увеличивает приоритет
                "learning_rate": 1.3,          # Улучшает обучение
                "motivation_boost": 1.4,       # Повышает мотивацию
                "reward_sensitivity": 1.6,     # Увеличивает чувствительность к награде
                "memory_consolidation": 1.2    # Улучшает консолидацию памяти
            },
            
            "serotonin": {
                "mood_stabilization": 1.0,     # Стабилизирует настроение
                "anxiety_reduction": 0.7,      # Снижает тревожность
                "impulse_control": 1.2,        # Улучшает контроль импульсов
                "social_processing": 1.3,      # Улучшает социальную обработку
                "emotional_regulation": 1.4    # Улучшает эмоциональную регуляцию
            },
            
            "norepinephrine": {
                "attention_focus": 1.6,        # Улучшает фокус внимания
                "stress_response": 1.8,        # Усиливает стрессовую реакцию
                "memory_encoding": 1.4,        # Улучшает кодирование памяти
                "arousal_level": 1.5,          # Повышает уровень возбуждения
                "alertness": 1.7               # Повышает бдительность
            },
            
            "acetylcholine": {
                "learning_enhancement": 1.5,   # Улучшает обучение
                "attention_switching": 1.3,    # Улучшает переключение внимания
                "memory_retrieval": 1.4,       # Улучшает извлечение памяти
                "cognitive_flexibility": 1.2,  # Повышает когнитивную гибкость
                "pattern_recognition": 1.3     # Улучшает распознавание паттернов
            },
            
            "gaba": {
                "anxiety_reduction": 0.5,      # Сильно снижает тревожность
                "inhibition_control": 1.3,     # Улучшает контроль торможения
                "relaxation": 0.6,             # Способствует расслаблению
                "sleep_quality": 1.2,          # Улучшает качество сна
                "emotional_dampening": 0.8     # Смягчает эмоциональные реакции
            }
        },
        
        "activation_conditions": {
            "dopamine": {
                "positive_valence_threshold": 0.3,
                "confidence_threshold": 0.6,
                "reward_emotions": ["joy", "trust", "anticipation"],
                "multiplier_formula": "min(1.0, (valence + confidence) / 2.0)"
            },
            
            "serotonin": {
                "stabilization_emotions": ["joy", "trust"],
                "neutral_valence_range": [-0.3, 0.3],
                "base_activation": 0.3,
                "formula": "max(0.3, 1.0 - abs(valence))"
            },
            
            "norepinephrine": {
                "stress_emotions": ["fear", "anger"],
                "high_arousal_threshold": 0.7,
                "activation_threshold": 0.6,
                "formula": "max(arousal, confidence if emotion in stress_emotions else 0)"
            },
            
            "acetylcholine": {
                "learning_emotions": ["surprise", "anticipation"],
                "high_confidence_threshold": 0.7,
                "activation_threshold": 0.5,
                "formula": "max(confidence, arousal if emotion == surprise else 0.5)"
            },
            
            "gaba": {
                "high_arousal_threshold": 0.8,
                "inhibition_emotions": ["anger"],
                "activation_threshold": 0.4,
                "formula": "min(1.0, arousal * 0.8)"
            }
        }
    }


def get_comprehensive_emotion_analysis_config() -> dict:
    """Возвращает полную конфигурацию анализа эмоций"""
    return {
        "intensity_modifiers": {
            # Усилители
            "очень": 1.5, "крайне": 1.8, "чрезвычайно": 2.0, "невероятно": 1.9,
            "супер": 1.6, "мега": 1.7, "ультра": 1.8, "гипер": 1.9,
            "безумно": 1.8, "дико": 1.7, "жутко": 1.6, "страшно": 1.5,
            "ужасно": 1.7, "кошмарно": 1.8, "адски": 1.9, "пиздец": 2.0,
            
            # English intensifiers
            "very": 1.5, "extremely": 2.0, "incredibly": 1.9, "super": 1.6,
            "mega": 1.7, "ultra": 1.8, "hyper": 1.9, "insanely": 1.8,
            "terribly": 1.7, "awfully": 1.7, "damn": 1.6, "fucking": 2.0,
            
            # Ослабители
            "немного": 0.6, "слегка": 0.5, "чуть": 0.4, "едва": 0.3,
            "почти": 0.7, "практически": 0.8, "довольно": 0.8,
            "относительно": 0.7, "сравнительно": 0.7, "несколько": 0.6,
            
            # English diminishers
            "slightly": 0.5, "somewhat": 0.6, "rather": 0.8, "quite": 0.8,
            "relatively": 0.7, "fairly": 0.8, "pretty": 0.8, "kind of": 0.6,
            "sort of": 0.6, "a bit": 0.4, "a little": 0.4,
            
            # Нейтральные
            "просто": 1.0, "обычно": 1.0, "нормально": 1.0,
            "just": 1.0, "simply": 1.0, "normally": 1.0, "usually": 1.0
        },
        
        "negation_words": {
            "russian": ["не", "нет", "никогда", "нисколько", "отнюдь", "вовсе", "никак", "ни"],
            "english": ["not", "no", "never", "nothing", "none", "neither", "nor"]
        },
        
        "amplifiers": {
            "russian": ["очень", "крайне", "чрезвычайно", "невероятно", "супер", "мега"],
            "english": ["very", "extremely", "incredibly", "super", "mega", "ultra"]
        },
        
        "diminishers": {
            "russian": ["немного", "слегка", "чуть", "едва", "почти", "практически"],
            "english": ["slightly", "somewhat", "rather", "quite", "a bit", "a little"]
        },
        
        "emotion_mapping": {
            "positive_emotions": ["joy", "trust", "anticipation"],
            "negative_emotions": ["sadness", "anger", "fear", "disgust"],
            "high_arousal_emotions": ["anger", "fear", "joy", "surprise"],
            "low_arousal_emotions": ["sadness", "trust"],
            "opposite_pairs": [
                ["joy", "sadness"],
                ["anger", "trust"],
                ["fear", "anticipation"],
                ["surprise", "neutral"]
            ]
        },
        
        "intensity_thresholds": {
            "very_high": 0.8,
            "high": 0.6,
            "medium": 0.4,
            "low": 0.2,
            "very_low": 0.0
        },
        
        "context_analysis": {
            "window_size": 3,  # Количество слов для контекстного анализа
            "negation_window": 5,  # Окно для обработки отрицаний
            "modifier_window": 4,  # Окно для применения модификаторов
            "confidence_boost": 1.2,  # Усиление при совпадении эмоций в контексте
            "confidence_penalty": 0.8  # Штраф при противоположных эмоциях
        },
        
        "history_settings": {
            "max_history_size": 50,
            "trend_analysis_hours": 24,
            "decay_factor": 0.95  # Фактор затухания для старых эмоций
        }
    }


def get_default_emotional_settings_for_agent(agent_name: str) -> dict:
    """Возвращает настройки эмоциональной памяти по умолчанию для агента"""
    base_config = {
        "emotion_triggers": get_comprehensive_emotion_triggers(),
        "neuromodulator_settings": get_comprehensive_neuromodulator_settings(),
        "emotion_analysis_config": get_comprehensive_emotion_analysis_config()
    }
    
    # Специализация по типу агента
    if "tech" in agent_name.lower():
        # Технический агент - больше фокуса на обучении и решении проблем
        base_config["neuromodulator_settings"]["base_levels"]["acetylcholine"] = 0.7
        base_config["neuromodulator_settings"]["base_levels"]["dopamine"] = 0.6
        base_config["neuromodulator_settings"]["activation_thresholds"]["acetylcholine"] = 0.4
        
    elif "support" in agent_name.lower():
        # Агент поддержки - больше эмпатии и стабилизации
        base_config["neuromodulator_settings"]["base_levels"]["serotonin"] = 0.8
        base_config["neuromodulator_settings"]["base_levels"]["gaba"] = 0.7
        base_config["neuromodulator_settings"]["activation_thresholds"]["serotonin"] = 0.2
        
    elif "research" in agent_name.lower():
        # Исследовательский агент - любопытство и обучение
        base_config["neuromodulator_settings"]["base_levels"]["acetylcholine"] = 0.8
        base_config["neuromodulator_settings"]["base_levels"]["dopamine"] = 0.7
        
    elif "creative" in agent_name.lower():
        # Креативный агент - больше гибкости и открытости
        base_config["neuromodulator_settings"]["base_levels"]["dopamine"] = 0.8
        base_config["neuromodulator_settings"]["modulation_effects"]["dopamine"]["learning_rate"] = 1.5
        
    return base_config


def migrate_database():
    """Выполняет миграцию базы данных"""
    try:
        engine = create_engine(DATABASE_URL)
        
        # Добавляем новые колонки
        with engine.connect() as connection:
            # Проверяем, существуют ли уже колонки
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'agent_summarization_settings' 
                AND column_name IN ('emotion_triggers', 'neuromodulator_settings', 'emotion_analysis_config')
            """))
            
            existing_columns = [row[0] for row in result]
            
            if 'emotion_triggers' not in existing_columns:
                connection.execute(text("""
                    ALTER TABLE agent_summarization_settings 
                    ADD COLUMN emotion_triggers JSON DEFAULT '{}'::json
                """))
                logger.info("✅ Добавлена колонка emotion_triggers")
            
            if 'neuromodulator_settings' not in existing_columns:
                connection.execute(text("""
                    ALTER TABLE agent_summarization_settings 
                    ADD COLUMN neuromodulator_settings JSON DEFAULT '{}'::json
                """))
                logger.info("✅ Добавлена колонка neuromodulator_settings")
            
            if 'emotion_analysis_config' not in existing_columns:
                connection.execute(text("""
                    ALTER TABLE agent_summarization_settings 
                    ADD COLUMN emotion_analysis_config JSON DEFAULT '{}'::json
                """))
                logger.info("✅ Добавлена колонка emotion_analysis_config")
            
            connection.commit()
        
        # Обновляем существующие записи с настройками по умолчанию
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Получаем всех агентов
            result = session.execute(text("SELECT agent_name FROM agent_summarization_settings"))
            agents = [row[0] for row in result]
            
            for agent_name in agents:
                emotional_settings = get_default_emotional_settings_for_agent(agent_name)
                
                session.execute(text("""
                    UPDATE agent_summarization_settings 
                    SET 
                        emotion_triggers = :emotion_triggers,
                        neuromodulator_settings = :neuromodulator_settings,
                        emotion_analysis_config = :emotion_analysis_config,
                        updated_at = CURRENT_TIMESTAMP,
                        version = version + 1
                    WHERE agent_name = :agent_name
                """), {
                    "agent_name": agent_name,
                    "emotion_triggers": json.dumps(emotional_settings["emotion_triggers"]),
                    "neuromodulator_settings": json.dumps(emotional_settings["neuromodulator_settings"]),
                    "emotion_analysis_config": json.dumps(emotional_settings["emotion_analysis_config"])
                })
                
                logger.info(f"✅ Обновлены настройки эмоциональной памяти для агента: {agent_name}")
            
            session.commit()
            logger.info("🎉 Миграция эмоциональной памяти завершена успешно!")
            
            # Статистика
            total_triggers = sum(len(triggers) for triggers in get_comprehensive_emotion_triggers().values())
            logger.info(f"📊 Добавлено {total_triggers} эмоциональных триггеров")
            logger.info(f"🧠 Настроено 5 типов нейромодуляторов")
            logger.info(f"⚙️ Создано {len(get_comprehensive_emotion_analysis_config())} конфигурационных параметров")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка при обновлении данных: {e}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_database()
