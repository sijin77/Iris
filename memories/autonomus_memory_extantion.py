"""Ключевые улучшения:
Автономные функции:
Эмоциональный анализ через EmotionAnalyzer
Детекция триггеров через TriggerDetector
Система самоуправляемых правил

Динамические индексы:
Эмоциональный индекс (ZSET)
Индекс важности с decay-фактором

Гибкая интеграция:
Декоратор для add_fragment
Добавление новых методов к существующему классу

Контекстный поиск:
Эмоционально релевантный контекст
Семантический поиск через LongTermMemory

Состояние системы:
Трекер уровня автономии
Мониторинг активных правил

Система самоуправляемых правил:
Условия и действия
Динамическое обновление

Эмоциональный анализ:
Вес эмоциональной составляющей
Эмоциональный индекс

Механизм забывания:
Memory decay rate
Динамическая важность

Автономный контекст:
Подбор релевантных фрагментов
Анализ текущего состояния

Триггеры и анализ:
Детекция ключевых фраз

Автоматическая оценка важности

Пример использования:
# 1. Инициализация базовой памяти
memory = WorkingMemory(...)

# 2. Добавление автономных функций
AutonomousMemoryExtension.enhance(memory)

# 3. Использование
fragment = MemoryFragment(...)
await memory.add_fragment(fragment)  # Будет автономно обработан

# Получение автономного контекста
context = await memory.get_autonomous_context("важное сообщение")
Что было перенесено из старой реализации:

Этот подход сохраняет все преимущества новой архитектуры, добавляя критически важные функции автономной работы из старой реализации.

"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import aioredis
from pydantic import BaseModel
import asyncio
from memories.S3_memory import AutonomousS3Memory
from memories.redis.redis_memory import WorkingMemory
from model.memory_fragment import MemoryFragment


class AutonomousMemoryExtension:
    """Дополнительные функции автономной памяти"""

    def __init__(self, memory: WorkingMemory):
        self.memory = memory
        self.config = AutonomousMemoryConfig()
        self.self_rules: List[SelfRule] = []
        self._init_autonomous_features()

    def _init_autonomous_features(self):
        """Инициализация автономных функций"""
        # 1. Индексы в Redis
        self.emotional_index_key = f"{self.memory.prefix}:emotional_index"
        self.importance_index_key = f"{self.memory.prefix}:importance_index"

        # 2. Загрузка правил
        self._load_initial_rules()

        # 3. Инициализация анализаторов
        self.emotion_analyzer = EmotionAnalyzer()
        self.trigger_detector = TriggerDetector()

    async def process_fragment(self, fragment: MemoryFragment) -> MemoryFragment:
        """Автономная обработка фрагмента"""
        # 1. Анализ эмоций и триггеров
        fragment.metadata.update(
            {
                "emotional_weight": self._analyze_emotion(fragment.content),
                "self_triggers": self._detect_triggers(fragment.content),
                "self_analysis": self._generate_analysis(fragment),
            }
        )

        # 2. Расчет важности
        importance = self._calculate_importance(fragment)
        fragment.priority = max(fragment.priority, importance)

        # 3. Обновление индексов
        await self._update_autonomous_indices(fragment, importance)

        # 4. Применение правил
        await self._apply_self_rules(fragment)

        return fragment

    async def get_autonomous_context(self, query: str) -> Dict:
        """Автономный подбор контекста"""
        return {
            "emotional": await self._get_emotional_context(),
            "semantic": (
                await self.memory.long_term_memory.search(query)
                if self.memory.long_term_memory
                else []
            ),
            "self_state": self._get_self_state(),
        }

    # ========== Основные автономные функции ==========
    async def _update_autonomous_indices(
        self, fragment: MemoryFragment, importance: float
    ):
        """Обновление автономных индексов"""
        pipe = self.memory.redis.pipeline()

        # Эмоциональный индекс
        if fragment.metadata["emotional_weight"] > 0.5:
            pipe.zadd(
                self.emotional_index_key,
                {fragment.id: fragment.metadata["emotional_weight"]},
            )

        # Индекс важности с decay-фактором
        adjusted_importance = importance * (1 - self.config.memory_decay_rate)
        pipe.zadd(self.importance_index_key, {fragment.id: adjusted_importance})

        await pipe.execute()

    async def _apply_self_rules(self, fragment: MemoryFragment):
        """Применение самоуправляемых правил"""
        for rule in self.self_rules:
            if self._evaluate_rule(rule, fragment):
                await self._execute_rule_action(rule, fragment)

    # ========== Аналитические методы ==========
    def _calculate_importance(self, fragment: MemoryFragment) -> float:
        """Комплексная оценка важности"""
        base = min(len(fragment.content) / 1000, 0.7)
        emotional = (
            fragment.metadata["emotional_weight"] * self.config.emotional_impact_weight
        )
        return min(base + emotional, 1.0)

    def _generate_analysis(self, fragment: MemoryFragment) -> str:
        """Генерация автономного анализа"""
        analysis = []
        if fragment.metadata["emotional_weight"] > 0.7:
            analysis.append("Эмоционально значимое сообщение")
        if any(t in fragment.metadata["self_triggers"] for t in ["важно", "срочно"]):
            analysis.append("Содержит важные триггеры")
        return " | ".join(analysis) if analysis else "Нейтральное сообщение"

    # ========== Контекстные методы ==========
    async def _get_emotional_context(self, limit: int = 3) -> List[MemoryFragment]:
        """Получение эмоционально значимого контекста"""
        ids = await self.memory.redis.zrevrange(self.emotional_index_key, 0, limit - 1)
        return await self.memory.get_fragments_by_ids([id.decode() for id in ids])

    def _get_self_state(self) -> Dict:
        """Текущее состояние автономной системы"""
        return {
            "autonomy_level": 0.3 + len(self.self_rules) * 0.05,
            "active_rules": [r.dict() for r in self.self_rules],
            "memory_decay_rate": self.config.memory_decay_rate,
        }

    # ========== Интеграция с EnhancedMemory ==========
    @classmethod
    def enhance(cls, memory: WorkingMemory) -> WorkingMemory:
        """Добавляет автономные функции к существующей памяти"""
        extension = cls(memory)

        # Сохраняем оригинальный метод
        original_add = memory.add_fragment

        async def enhanced_add(fragment: MemoryFragment):
            processed = await extension.process_fragment(fragment)
            return await original_add(processed)

        memory.add_fragment = enhanced_add
        memory.get_autonomous_context = extension.get_autonomous_context

        return memory
