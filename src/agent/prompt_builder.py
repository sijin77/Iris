"""
PromptBuilder - модуль для детерминированной сборки промптов агента.

Этот модуль отвечает за:
1. Структурированную сборку промптов из компонентов профиля
2. Контроль длины и приоритетов компонентов
3. Безопасность и фильтрацию контента
4. Консистентность личности агента
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from agent.models import AgentProfile

logger = logging.getLogger(__name__)

@dataclass
class PromptComponents:
    """Компоненты для сборки промпта"""
    system_prompt: str
    persona_traits: str
    safety_rules: str
    context: str
    user_message: str
    conversation_history: str = ""
    
    def __post_init__(self):
        """Валидация компонентов после инициализации"""
        if not self.system_prompt:
            raise ValueError("system_prompt не может быть пустым")
        if not self.user_message:
            raise ValueError("user_message не может быть пустым")

class PromptBuilder:
    """
    Сборщик промптов для агента.
    
    Обеспечивает:
    - Детерминированную структуру промпта
    - Контроль длины компонентов
    - Приоритизацию важных частей
    - Безопасность и фильтрацию
    """
    
    def __init__(self, max_total_length: int = 4000, max_context_length: int = 1000):
        """
        Инициализация сборщика промптов.
        
        Args:
            max_total_length: Максимальная общая длина промпта
            max_context_length: Максимальная длина контекста
        """
        self.max_total_length = max_total_length
        self.max_context_length = max_context_length
        
        # Приоритеты компонентов (чем выше, тем важнее)
        self.component_priorities = {
            'system_prompt': 100,
            'persona_traits': 90,
            'safety_rules': 85,
            'user_message': 80,
            'context': 60,
            'conversation_history': 40
        }
    
    def build_prompt(self, profile: AgentProfile, components: PromptComponents) -> str:
        """
        Сборка финального промпта из компонентов профиля.
        
        Args:
            profile: Профиль агента
            components: Компоненты для сборки
            
        Returns:
            Собранный промпт в формате строки
        """
        try:
            # Собираем базовые компоненты профиля
            prompt_parts = []
            
            # 1. Системные инструкции (высший приоритет)
            if profile.system_prompt:
                prompt_parts.append(f"[System Instructions]\n{profile.system_prompt}")
            
            # 2. Черты личности
            if profile.persona_traits:
                prompt_parts.append(f"[Personality]\n{profile.persona_traits}")
            
            # 3. Правила безопасности
            if profile.safety_rules:
                prompt_parts.append(f"[Safety Rules]\n{profile.safety_rules}")
            
            # 4. Контекст (если есть)
            if components.context:
                context_part = self._truncate_text(components.context, self.max_context_length)
                prompt_parts.append(f"[Context]\n{context_part}")
            
            # 5. История диалога (если есть)
            if components.conversation_history:
                history_part = self._truncate_text(components.conversation_history, 800)
                prompt_parts.append(f"[Conversation History]\n{history_part}")
            
            # 6. Сообщение пользователя
            prompt_parts.append(f"[User]\n{components.user_message}")
            
            # 7. Инструкция для ответа
            response_instruction = self._build_response_instruction(profile)
            prompt_parts.append(f"[Response Instructions]\n{response_instruction}")
            
            # Собираем финальный промпт
            final_prompt = "\n\n".join(prompt_parts)
            
            # Проверяем общую длину
            if len(final_prompt) > self.max_total_length:
                final_prompt = self._truncate_prompt(final_prompt, profile)
            
            logger.debug(f"Промпт собран: {len(final_prompt)} символов")
            return final_prompt
            
        except Exception as e:
            logger.error(f"Ошибка сборки промпта: {e}")
            # Fallback на простой промпт
            return f"[User]\n{components.user_message}\n\n[Assistant]\n"
    
    def _build_response_instruction(self, profile: AgentProfile) -> str:
        """
        Сборка инструкций для ответа на основе профиля.
        
        Args:
            profile: Профиль агента
            
        Returns:
            Инструкции для ответа
        """
        instructions = []
        
        # Тон общения
        if profile.tone:
            tone_map = {
                "formal": "Отвечай формально и профессионально",
                "friendly": "Отвечай дружелюбно и тепло",
                "casual": "Отвечай неформально и легко",
                "professional": "Отвечай профессионально, но доступно"
            }
            tone_instruction = tone_map.get(profile.tone, "Отвечай в своём стиле")
            instructions.append(tone_instruction)
        
        # Стиль отказа
        if profile.refusal_style:
            refusal_map = {
                "polite": "При отказе будь вежливым и объясни причину",
                "firm": "При отказе будь твёрдым, но уважительным",
                "humorous": "При отказе можешь использовать юмор, но не теряй серьёзность"
            }
            refusal_instruction = refusal_map.get(profile.refusal_style, "При отказе объясни причину")
            instructions.append(refusal_instruction)
        
        # Подпись и эмодзи
        if profile.signature or profile.emoji:
            signature_part = []
            if profile.emoji:
                signature_part.append(profile.emoji)
            if profile.signature:
                signature_part.append(profile.signature)
            instructions.append(f"Заверши ответ: {' '.join(signature_part)}")
        
        # Базовые инструкции
        instructions.extend([
            "Оставайся в рамках своей личности",
            "Отвечай по существу, но не теряй индивидуальность",
            "Если не уверен - честно скажи об этом"
        ])
        
        return ". ".join(instructions) + "."
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """
        Обрезка текста до максимальной длины с сохранением смысла.
        
        Args:
            text: Исходный текст
            max_length: Максимальная длина
            
        Returns:
            Обрезанный текст
        """
        if len(text) <= max_length:
            return text
        
        # Пытаемся обрезать по предложениям
        sentences = text.split('. ')
        truncated = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) + 2 <= max_length:
                truncated.append(sentence)
                current_length += len(sentence) + 2
            else:
                break
        
        if truncated:
            return '. '.join(truncated) + '.'
        
        # Если не удалось по предложениям, обрезаем по словам
        words = text.split()
        truncated_words = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_length:
                truncated_words.append(word)
                current_length += len(word) + 1
            else:
                break
        
        return ' '.join(truncated_words)
    
    def _truncate_prompt(self, prompt: str, profile: AgentProfile) -> str:
        """
        Умная обрезка промпта с сохранением критически важных частей.
        
        Args:
            prompt: Исходный промпт
            profile: Профиль агента
            
        Returns:
            Обрезанный промпт
        """
        # Приоритет: system_prompt > persona_traits > user_message > context > history
        parts = prompt.split('\n\n')
        
        # Оставляем только критически важные части
        essential_parts = []
        current_length = 0
        
        for part in parts:
            if '[System Instructions]' in part or '[Personality]' in part:
                essential_parts.append(part)
                current_length += len(part) + 2
            elif '[User]' in part:
                essential_parts.append(part)
                current_length += len(part) + 2
            elif current_length + len(part) + 2 <= self.max_total_length:
                essential_parts.append(part)
                current_length += len(part) + 2
        
        return '\n\n'.join(essential_parts)
    
    def get_generation_settings(self, profile: AgentProfile) -> Dict:
        """
        Получение параметров генерации из профиля.
        
        Args:
            profile: Профиль агента
            
        Returns:
            Словарь с параметрами генерации
        """
        try:
            if profile.gen_settings:
                return json.loads(profile.gen_settings)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Ошибка парсинга gen_settings: {e}")
        
        # Дефолтные параметры
        return {
            "temperature": 0.7,
            "top_p": 0.9,
            "stop_words": ["</s>", "\nUser:", "---", "###"],
            "max_tokens": 512
        }
