"""
Миграция для создания таблицы настроек суммаризации агентов.
Добавляет возможность персонализации паттернов и параметров чанкинга.
"""

import sys
import os
import logging
from datetime import datetime

# Добавляем путь к src для импорта моделей
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from agent.models_extended import AgentSummarizationSettings, Base
from config.settings import get_database_url

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_specialized_config_for_agent(agent_name: str, agent_role: str) -> dict:
    """
    Создает специализированную конфигурацию в зависимости от роли агента
    """
    # Базовая конфигурация с максимальными возможностями
    base_config = get_comprehensive_base_config()
    
    # Специализация по ролям
    if "technical" in agent_role.lower() or "tech" in agent_name.lower():
        return get_technical_agent_config(base_config)
    elif "support" in agent_role.lower() or "help" in agent_role.lower():
        return get_support_agent_config(base_config)
    elif "research" in agent_role.lower() or "analyst" in agent_role.lower():
        return get_research_agent_config(base_config)
    elif "creative" in agent_role.lower() or "content" in agent_role.lower():
        return get_creative_agent_config(base_config)
    else:
        # Универсальный агент (как Ириска)
        return get_universal_agent_config(base_config)


def get_comprehensive_base_config() -> dict:
    """Возвращает базовую конфигурацию с максимальными возможностями"""
    return {
        "enabled": True,
        "chunking_strategy": "hybrid",
        "max_chunk_size": 1024,
        "min_chunk_size": 50,
        "overlap_size": 100,
        "max_context_length": 4000,
        "retrieval_k": 12,
        "final_k": 6,
        "thresholds": {
            "high_importance": 0.75,
            "medium_importance": 0.4,
            "min_relevance": 0.15,
            "time_gap": 180
        },
        "weights": {
            "ranking": {"relevance": 0.6, "temporal": 0.25, "importance": 0.15},
            "temporal": {"very_recent": 1.0, "recent": 0.85, "medium": 0.5, "old": 0.2},
            "importance": {
                "high_keywords": 0.35, "medium_keywords": 0.2, "message_length": 0.15,
                "question_marks": 0.12, "exclamation_marks": 0.08, "caps_ratio": 0.05,
                "user_feedback": 0.05
            }
        },
        "patterns": get_comprehensive_patterns(),
        "user_modes": get_comprehensive_user_modes()
    }


def get_technical_agent_config(base_config: dict) -> dict:
    """Конфигурация для технического агента"""
    config = base_config.copy()
    config.update({
        "chunking_strategy": "topic_based",
        "max_chunk_size": 1200,
        "max_context_length": 5000,
        "thresholds": {
            **config["thresholds"],
            "high_importance": 0.8,
            "min_relevance": 0.2
        }
    })
    
    # Усиливаем технические паттерны
    patterns = config["patterns"].copy()
    patterns["technical_context"].extend([
        r"архитектура|architecture|дизайн|design|паттерн|pattern",
        r"производительность|performance|оптимизация|optimization",
        r"безопасность|security|уязвимость|vulnerability",
        r"масштабируемость|scalability|нагрузка|load|stress"
    ])
    
    patterns["importance_high"].extend([
        "рефакторинг", "refactoring", "код ревью", "code review",
        "архитектура", "architecture", "производительность", "performance"
    ])
    
    config["patterns"] = patterns
    return config


def get_support_agent_config(base_config: dict) -> dict:
    """Конфигурация для агента поддержки"""
    config = base_config.copy()
    config.update({
        "chunking_strategy": "context_based",
        "max_chunk_size": 600,
        "max_context_length": 2500,
        "weights": {
            **config["weights"],
            "ranking": {"relevance": 0.5, "temporal": 0.3, "importance": 0.2}
        }
    })
    
    # Усиливаем эмоциональные паттерны
    patterns = config["patterns"].copy()
    patterns["emotional_context"].extend([
        r"помощь|help|поддержка|support|ассистент|assistance",
        r"проблемы|problems|трудности|difficulties|вопросы|questions",
        r"решение|solution|совет|advice|рекомендация|recommendation"
    ])
    
    patterns["importance_high"].extend([
        "жалоба", "complaint", "недовольство", "dissatisfaction",
        "срочная помощь", "urgent help", "не могу", "can't", "не получается", "doesn't work"
    ])
    
    config["patterns"] = patterns
    return config


def get_research_agent_config(base_config: dict) -> dict:
    """Конфигурация для исследовательского агента"""
    config = base_config.copy()
    config.update({
        "chunking_strategy": "importance_based",
        "max_chunk_size": 1500,
        "max_context_length": 6000,
        "retrieval_k": 20,
        "final_k": 10,
        "thresholds": {
            **config["thresholds"],
            "high_importance": 0.85,
            "min_relevance": 0.25
        }
    })
    
    # Усиливаем исследовательские паттерны
    patterns = config["patterns"].copy()
    patterns["importance_high"].extend([
        "исследование", "research", "анализ", "analysis", "изучение", "study",
        "данные", "data", "статистика", "statistics", "метрики", "metrics",
        "тренды", "trends", "паттерны", "patterns", "корреляция", "correlation"
    ])
    
    patterns["questions"].extend([
        r"исследуй|research|изучи|study|проанализируй|analyze",
        r"сравни|compare|сопоставь|contrast|оцени|evaluate",
        r"какие тренды|what trends|какие данные|what data"
    ])
    
    config["patterns"] = patterns
    return config


def get_creative_agent_config(base_config: dict) -> dict:
    """Конфигурация для креативного агента"""
    config = base_config.copy()
    config.update({
        "chunking_strategy": "context_based",
        "max_chunk_size": 800,
        "max_context_length": 3500,
        "thresholds": {
            **config["thresholds"],
            "high_importance": 0.6,
            "medium_importance": 0.3
        }
    })
    
    # Добавляем креативные паттерны
    patterns = config["patterns"].copy()
    patterns["creative_context"] = [
        r"идея|idea|концепт|concept|творчество|creativity",
        r"дизайн|design|стиль|style|эстетика|aesthetics",
        r"вдохновение|inspiration|мотивация|motivation",
        r"инновация|innovation|оригинальность|originality",
        r"создай|create|придумай|come up with|сгенерируй|generate"
    ]
    
    patterns["importance_medium"].extend([
        "креатив", "creative", "артистический", "artistic",
        "визуальный", "visual", "концептуальный", "conceptual"
    ])
    
    config["patterns"] = patterns
    return config


def get_universal_agent_config(base_config: dict) -> dict:
    """Конфигурация для универсального агента (как Ириска)"""
    # Универсальный агент получает полную базовую конфигурацию
    return base_config


def get_comprehensive_patterns() -> dict:
    """Возвращает максимально полный набор паттернов"""
    return {
        "topic_shift": [
            # Прямые переходы к новой теме
            r"кстати|между прочим|а еще|теперь о|давай поговорим|поговорим о",
            r"другой вопрос|другая тема|переходим к|перейдем к|новая тема",
            r"забыл спросить|еще хотел|кстати да|а да|а кстати",
            r"а что насчет|а как же|а про|а относительно|что думаешь о",
            r"меняя тему|сменим тему|другое дело|иная тема|смена темы",
            r"кроме того|помимо этого|также|еще один момент|еще вопрос",
            r"в связи с этим|по этому поводу|касательно|насчет того",
            # Возвращение к предыдущим темам
            r"возвращаясь к|вернемся к|помнишь мы говорили|как мы обсуждали",
            r"то что мы говорили|наш разговор о|ранее упомянутое",
            r"как я говорил|как ты сказал|помнишь ты упоминал",
            # Ассоциативные переходы
            r"это напоминает|это как|похоже на|аналогично",
            r"в том же духе|по аналогии|схожая ситуация|подобный случай",
            r"это заставляет думать|наводит на мысль|приходит на ум",
            # Контрастные переходы
            r"в отличие от|в противоположность|наоборот|с другой стороны",
            r"но если|а что если|представь что|допустим что",
            r"иначе говоря|другими словами|то есть|проще говоря",
            # Временные переходы
            r"сначала|потом|затем|после этого|в итоге|в конце концов",
            r"до этого|перед тем|раньше|позже|впоследствии",
            r"тем временем|одновременно|параллельно|в то же время",
            # Причинно-следственные переходы
            r"поэтому|следовательно|из-за этого|в результате|отсюда",
            r"благодаря этому|вследствие|по причине|ввиду того",
            r"что приводит к|что означает|что говорит о|что свидетельствует",
            # Уточняющие переходы
            r"точнее|конкретнее|детальнее|подробнее|если быть точным",
            r"уточню|поясню|объясню|расскажу подробнее|дам пример",
            r"имею в виду|хочу сказать|суть в том|дело в том",
            # Английские прямые переходы
            r"by the way|speaking of|on another note|changing topics",
            r"new topic|different question|another thing|also|additionally",
            r"while we're at it|incidentally|that reminds me|come to think of it",
            r"moving on|next question|something else|one more thing|another matter",
            # Английские возвращения
            r"getting back to|returning to|as we discussed|as mentioned before",
            r"remember when|you said earlier|we talked about|previously mentioned",
            r"going back to|circling back|as I was saying|as you pointed out",
            # Английские ассоциативные
            r"this reminds me|it's like|similar to|analogous to|comparable to",
            r"in the same vein|along those lines|related to this|on a similar note",
            r"this makes me think|brings to mind|calls to mind|suggests",
            # Английские контрастные
            r"in contrast|on the contrary|conversely|however|nevertheless",
            r"but what if|suppose that|imagine if|let's say|hypothetically",
            r"in other words|that is to say|namely|specifically|put differently",
            # Английские временные
            r"first|then|next|after that|finally|in the end|ultimately",
            r"before that|previously|earlier|later|subsequently|afterwards",
            r"meanwhile|simultaneously|at the same time|concurrently",
            # Английские причинно-следственные
            r"therefore|thus|consequently|as a result|hence|accordingly",
            r"due to this|because of this|thanks to|owing to|given that",
            r"which leads to|which means|which indicates|which suggests",
            # Английские уточняющие
            r"more precisely|specifically|in detail|to be exact|to clarify",
            r"let me explain|let me elaborate|for example|for instance|such as",
            r"I mean|what I'm saying is|the point is|the thing is|essentially"
        ],
        "questions": [
            # Вопросы о состоянии и самочувствии
            r"как\s+(?:дела|настроение|ты|вы|поживаешь|самочувствие|жизнь|работа)",
            r"что\s+(?:думаешь|скажешь|посоветуешь|предложишь|считаешь|чувствуешь)",
            r"можешь\s+(?:помочь|рассказать|объяснить|показать|научить|подсказать)",
            r"расскажи\s+(?:про|о|мне|подробнее|больше|как|что)",
            r"как\s+(?:себя чувствуешь|твои дела|прошел день|настроение|успехи)",
            r"что\s+(?:нового|интересного|случилось|произошло|изменилось)",
            r"все\s+(?:хорошо|в порядке|нормально|отлично|замечательно)",
            # Технические вопросы
            r"как\s+(?:работает|устроено|делается|настроить|установить|запустить|использовать)",
            r"что\s+(?:такое|значит|означает|представляет|собой|делает|происходит)",
            r"где\s+(?:находится|можно|лучше|искать|смотреть|найти|посмотреть)",
            r"когда\s+(?:лучше|нужно|можно|стоит|следует|использовать|применять)",
            r"почему\s+(?:так|не работает|происходит|нужно|важно|случилось|получается)",
            r"зачем\s+(?:нужно|это|делать|использовать|применять|изучать)",
            r"сколько\s+(?:стоит|времени|нужно|требуется|занимает|длится)",
            r"какой\s+(?:лучше|выбрать|использовать|подойдет|рекомендуешь)",
            # Вопросы-просьбы
            r"можно\s+(?:ли|попросить|узнать|спросить|уточнить|выяснить)",
            r"не\s+(?:мог бы|могла бы|можешь|поможешь|подскажешь|объяснишь)",
            r"помоги\s+(?:мне|разобраться|понять|решить|найти|выбрать)",
            r"подскажи\s+(?:как|что|где|когда|почему|зачем|сколько)",
            r"объясни\s+(?:мне|как|что|почему|зачем|принцип|суть)",
            # Исследовательские вопросы
            r"интересно\s+(?:узнать|знать|выяснить|понять|разобраться)",
            r"хотелось бы\s+(?:узнать|понять|разобраться|выяснить|изучить)",
            r"любопытно\s+(?:как|что|почему|зачем|где|когда)",
            r"а\s+(?:правда ли|действительно|так ли|верно ли|возможно ли)",
            r"есть ли\s+(?:способ|возможность|вариант|метод|решение)",
            # Сравнительные вопросы
            r"что\s+(?:лучше|хуже|эффективнее|быстрее|надежнее|безопаснее)",
            r"какой\s+(?:из|вариант|способ|метод|подход|решение)\s+(?:лучше|предпочтительнее)",
            r"в чем\s+(?:разница|отличие|преимущество|недостаток|особенность)",
            r"чем\s+(?:отличается|лучше|хуже|отличается|выделяется)",
            # Проблемные вопросы
            r"что\s+(?:делать если|случится если|произойдет если|будет если)",
            r"как\s+(?:исправить|решить|устранить|избежать|предотвратить)",
            r"почему\s+(?:не получается|не работает|ошибка|проблема|сбой)",
            r"что\s+(?:не так|неправильно|пошло не так|случилось|произошло)",
            # Планирующие вопросы
            r"что\s+(?:планируешь|собираешься|хочешь|намереваешься|думаешь делать)",
            r"как\s+(?:планируешь|собираешься|хочешь|думаешь|намереваешься)",
            r"когда\s+(?:планируешь|собираешься|хочешь|думаешь|намереваешься)",
            r"где\s+(?:планируешь|собираешься|хочешь|думаешь|намереваешься)",
            # Английские базовые вопросы
            r"how\s+(?:do|does|can|to|about|is|are|did|will|would|should)",
            r"what\s+(?:is|are|do|does|about|if|when|where|why|how)",
            r"where\s+(?:is|are|can|do|to|should|will|would|did)",
            r"when\s+(?:is|do|should|can|to|will|would|did|does)",
            r"why\s+(?:is|do|does|should|can|not|don't|didn't|won't)",
            r"who\s+(?:is|are|can|should|will|would|did|does|has)",
            r"which\s+(?:is|are|one|way|method|option|choice|better)",
            r"whose\s+(?:is|are|idea|fault|responsibility|job|turn)",
            # Английские вопросы о состоянии
            r"how\s+(?:are you|do you feel|is it going|was your day)",
            r"what's\s+(?:up|new|happening|going on|the matter|wrong)",
            r"are you\s+(?:okay|alright|fine|good|well|feeling)",
            r"is everything\s+(?:okay|alright|fine|good|well)",
            # Английские технические вопросы
            r"how\s+(?:does it work|to use|to install|to configure|to setup)",
            r"what\s+(?:does it do|is it for|does it mean|happens if)",
            r"where\s+(?:can I find|should I look|is it located|do I put)",
            r"when\s+(?:should I use|is it best|do I need|will it)",
            r"why\s+(?:doesn't it work|is it important|do I need|should I)",
            # Английские вопросы-просьбы
            r"can you\s+(?:help|tell|show|explain|teach|guide)",
            r"could you\s+(?:help|tell|show|explain|please|possibly)",
            r"would you\s+(?:help|mind|please|be able|consider)",
            r"will you\s+(?:help|show|tell|explain|teach)",
            # Английские исследовательские вопросы
            r"I wonder\s+(?:if|how|what|why|when|where)",
            r"I'm curious\s+(?:about|how|what|why|if)",
            r"is it possible\s+(?:to|that|for)",
            r"do you think\s+(?:it's|that|we should|I should)",
            # Английские сравнительные вопросы
            r"what's\s+(?:better|worse|different|the difference|best)",
            r"which\s+(?:is better|would you choose|do you prefer|works best)",
            r"how\s+(?:does it compare|is it different|much better|much worse)",
            # Английские проблемные вопросы
            r"what\s+(?:if|should I do|went wrong|happened|'s the problem)",
            r"how\s+(?:to fix|to solve|to resolve|can I fix)",
            r"why\s+(?:isn't it working|did it fail|doesn't it work)",
            r"what's\s+(?:wrong|the issue|the problem|not working)"
        ],
        "completion": [
            # Понимание и осознание
            r"понятно|ясно|понял|поняла|разобрался|разобралась|дошло|осознал",
            r"теперь понимаю|теперь ясно|теперь вижу|теперь знаю|теперь понял",
            r"ага|ах да|а понял|а ясно|а теперь понятно|а теперь вижу",
            r"точно|именно|верно|правильно|так и есть|абсолютно верно",
            r"логично|разумно|обоснованно|справедливо|правомерно",
            # Благодарность и признательность
            r"спасибо|благодарю|благодарен|признателен|очень благодарен",
            r"большое спасибо|огромное спасибо|сердечно благодарю|от души спасибо",
            r"спасибо за помощь|спасибо за объяснение|спасибо за совет|спасибо за время",
            r"ценю твою помощь|ценю поддержку|ценю совет|ценю объяснение",
            # Положительная оценка
            r"отлично|хорошо|супер|замечательно|прекрасно|великолепно|шикарно",
            r"классно|круто|здорово|потрясающе|восхитительно|изумительно",
            r"именно то что нужно|то что искал|идеально|превосходно",
            r"лучше не придумаешь|не мог и мечтать|выше всех похвал",
            # Полное понимание
            r"все ясно|все понял|все поняла|все понятно|все встало на места",
            r"картина прояснилась|стало понятно|разложилось по полочкам",
            r"теперь все сходится|теперь все логично|теперь все на своих местах",
            r"пазл сложился|мозаика сложилась|все кусочки встали на места",
            # Завершение задачи
            r"достаточно|хватит|довольно|более чем достаточно|этого хватит",
            r"все|всё|это все|больше ничего|ничего больше не нужно",
            r"закончили|завершили|сделали|выполнили|решили|разобрались",
            r"задача решена|вопрос закрыт|проблема решена|дело сделано",
            r"цель достигнута|результат получен|итог подведен|финиш",
            # Удовлетворение результатом
            r"доволен результатом|удовлетворен|результат радует|все получилось",
            r"то что нужно|именно это|как раз то|точно в цель|в точку",
            r"не ожидал такого|превзошло ожидания|лучше чем думал",
            # Готовность к действию
            r"готов|готова|можно начинать|можно приступать|пора действовать",
            r"теперь знаю что делать|теперь план ясен|теперь путь понятен",
            r"вперед|поехали|начинаем|приступаем|в путь|за дело",
            # Английские - понимание и осознание
            r"got it|I see|understood|clear|makes sense|I get it",
            r"now I understand|now I see|now it's clear|now I know",
            r"ah I see|oh I get it|right|exactly|that's right|absolutely",
            r"it all makes sense now|everything clicks|it's all clear now",
            r"the penny dropped|it clicked|light bulb moment|aha moment",
            # Английские - благодарность
            r"thanks|thank you|appreciate|grateful|much appreciated",
            r"thanks a lot|thank you so much|really appreciate|very grateful",
            r"thanks for help|thanks for explaining|thanks for advice|thanks for time",
            r"I appreciate your help|appreciate the support|value your input",
            # Английские - положительная оценка
            r"perfect|great|excellent|wonderful|awesome|fantastic|brilliant",
            r"amazing|incredible|outstanding|superb|magnificent|marvelous",
            r"exactly what I needed|just what I was looking for|couldn't be better",
            r"beyond expectations|more than I hoped for|absolutely perfect",
            # Английские - полное понимание
            r"crystal clear|perfectly clear|completely understand|totally get it",
            r"everything makes sense|it all adds up|pieces fit together",
            r"the picture is clear|I have the full picture|everything falls into place",
            r"puzzle solved|mystery solved|all pieces together|complete picture",
            # Английские - завершение задачи
            r"enough|that's enough|sufficient|plenty|more than enough",
            r"that's all|that's it|done|finished|completed|wrapped up",
            r"mission accomplished|task complete|job done|problem solved",
            r"goal achieved|objective met|target reached|success",
            # Английские - удовлетворение
            r"satisfied|pleased|happy with result|content|fulfilled",
            r"just what I needed|exactly right|spot on|perfect match",
            r"exceeded expectations|better than expected|more than hoped",
            # Английские - готовность к действию
            r"ready|prepared|set to go|ready to start|let's do this",
            r"now I know what to do|plan is clear|path is clear|way forward",
            r"let's go|here we go|time to start|let's begin|off we go"
        ],
        "temporal_absolute": [
            # Дни - базовые
            r"вчера|сегодня|завтра|послезавтра|позавчера|третьего дня",
            r"на днях|в эти дни|в последние дни|в ближайшие дни",
            r"позавчера вечером|вчера утром|сегодня днем|завтра вечером",
            # Дни - английские
            r"yesterday|today|tomorrow|the day after tomorrow|the day before yesterday",
            r"these days|recent days|upcoming days|in recent days|in the coming days",
            r"yesterday morning|today afternoon|tomorrow evening|this morning",
            # Недели - русские
            r"на прошлой неделе|на этой неделе|на следующей неделе|на будущей неделе",
            r"неделю назад|через неделю|в течение недели|всю неделю|целую неделю",
            r"в начале недели|в середине недели|в конце недели|к концу недели",
            r"с начала недели|до конца недели|на выходных|в будни",
            # Недели - английские
            r"last week|this week|next week|the following week|the previous week",
            r"a week ago|in a week|during the week|all week|the whole week",
            r"early in the week|mid-week|end of week|by the end of week",
            r"since the beginning of week|until the end of week|on weekends|on weekdays",
            # Дни недели - русские полные
            r"в понедельник|во вторник|в среду|в четверг|в пятницу|в субботу|в воскресенье",
            r"в прошлый понедельник|в этот вторник|в следующую среду|в будущий четверг",
            r"каждый понедельник|по вторникам|по средам|по четвергам|по пятницам",
            r"с понедельника|до пятницы|с субботы по воскресенье|в выходные",
            # Дни недели - английские полные
            r"on monday|on tuesday|on wednesday|on thursday|on friday|on saturday|on sunday",
            r"last monday|this tuesday|next wednesday|the following thursday",
            r"every monday|on tuesdays|on wednesdays|on thursdays|on fridays",
            r"from monday|until friday|from saturday to sunday|on weekends",
            # Месяцы - русские
            r"в прошлом месяце|в этом месяце|в следующем месяце|в будущем месяце",
            r"месяц назад|через месяц|в течение месяца|весь месяц|целый месяц",
            r"в начале месяца|в середине месяца|в конце месяца|к концу месяца",
            r"с начала месяца|до конца месяца|в первой половине|во второй половине",
            # Месяцы - английские
            r"last month|this month|next month|the following month|the previous month",
            r"a month ago|in a month|during the month|all month|the whole month",
            r"early in the month|mid-month|end of month|by the end of month",
            r"since the beginning of month|until the end of month|first half|second half",
            # Конкретные месяцы - русские
            r"в январе|в феврале|в марте|в апреле|в мае|в июне",
            r"в июле|в августе|в сентябре|в октябре|в ноябре|в декабре",
            r"в прошлом январе|в этом феврале|в следующем марте",
            # Конкретные месяцы - английские
            r"in january|in february|in march|in april|in may|in june",
            r"in july|in august|in september|in october|in november|in december",
            r"last january|this february|next march|the following april",
            # Сезоны - русские
            r"весной|летом|осенью|зимой|в этом году|в прошлом году",
            r"прошлой весной|этим летом|следующей осенью|будущей зимой",
            r"в начале весны|в середине лета|в конце осени|глубокой зимой",
            # Сезоны - английские
            r"in spring|in summer|in autumn|in fall|in winter|this year|last year",
            r"last spring|this summer|next autumn|the following winter",
            r"early spring|mid-summer|late autumn|deep winter",
            # Годы - русские расширенные
            r"в прошлом году|в этом году|в следующем году|в будущем году",
            r"год назад|через год|в течение года|весь год|целый год",
            r"в начале года|в середине года|в конце года|к концу года",
            r"с начала года|до конца года|в первом полугодии|во втором полугодии",
            r"в позапрошлом году|два года назад|через два года|несколько лет назад",
            # Годы - английские расширенные
            r"last year|this year|next year|the following year|the previous year",
            r"a year ago|in a year|during the year|all year|the whole year",
            r"early in the year|mid-year|end of year|by the end of year",
            r"since the beginning of year|until the end of year|first half|second half",
            r"two years ago|in two years|several years ago|a few years back",
            # Конкретные даты и форматы
            r"\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}-\d{1,2}-\d{4}",
            r"\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}|\d{4}\.\d{2}\.\d{2}",
            r"\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)",
            r"\d{1,2}(?:st|nd|rd|th)\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)",
            # Праздники и особые даты - русские
            r"на новый год|на рождество|на пасху|на день рождения|на годовщину",
            r"в новогодние праздники|в рождественские каникулы|в пасхальные дни",
            r"в день победы|в день независимости|в международный день|в праздник",
            # Праздники и особые даты - английские
            r"on new year|on christmas|on easter|on birthday|on anniversary",
            r"during new year holidays|during christmas break|during easter days",
            r"on victory day|on independence day|on international day|on holiday",
            # Исторические периоды
            r"в детстве|в юности|в молодости|в зрелом возрасте|в старости",
            r"в школьные годы|в студенческие годы|в рабочие годы|на пенсии",
            r"in childhood|in youth|in young age|in mature age|in old age",
            r"during school years|during college years|during working years|in retirement"
        ],
        "temporal_relative": [
            # Время суток - детальное
            r"утром|днем|днём|вечером|ночью|рано утром|поздно вечером|глубокой ночью",
            r"на рассвете|на закате|в полдень|в полночь|перед рассветом|после заката",
            r"с утра до вечера|весь день|всю ночь|до утра|до вечера|до ночи",
            r"morning|afternoon|evening|night|early morning|late evening|deep night",
            r"at dawn|at sunset|at noon|at midnight|before dawn|after sunset",
            r"from morning till evening|all day|all night|until morning|until evening",
            # Относительное время - ближнее
            r"недавно|давно|скоро|потом|позже|раньше|сейчас|только что",
            r"совсем недавно|очень давно|совсем скоро|прямо сейчас|в данный момент",
            r"буквально только что|несколько мгновений назад|через мгновение",
            r"recently|long ago|soon|later|earlier|before|now|just now",
            r"very recently|very long ago|very soon|right now|at this moment",
            r"just a moment ago|a few moments ago|in a moment|any moment now",
            # Продолжительность - минуты и часы
            r"несколько секунд назад|минуту назад|пару минут назад|полчаса назад",
            r"час назад|пару часов назад|несколько часов назад|полдня назад",
            r"через секунду|через минуту|через полчаса|через час|через пару часов",
            r"a few seconds ago|a minute ago|a couple of minutes ago|half an hour ago",
            r"an hour ago|a couple of hours ago|several hours ago|half a day ago",
            r"in a second|in a minute|in half an hour|in an hour|in a couple of hours",
            # Продолжительность - дни и недели
            r"вчера утром|позавчера вечером|несколько дней назад|на днях",
            r"неделю назад|пару недель назад|несколько недель назад",
            r"через день|через пару дней|через неделю|через несколько недель",
            r"yesterday morning|day before yesterday evening|several days ago|the other day",
            r"a week ago|a couple of weeks ago|several weeks ago|a few weeks back",
            r"in a day|in a couple of days|in a week|in several weeks",
            # Продолжительность - месяцы и годы
            r"месяц назад|пару месяцев назад|несколько месяцев назад|полгода назад",
            r"год назад|пару лет назад|несколько лет назад|много лет назад",
            r"через месяц|через полгода|через год|через несколько лет",
            r"a month ago|a couple of months ago|several months ago|half a year ago",
            r"a year ago|a couple of years ago|several years ago|many years ago",
            r"in a month|in half a year|in a year|in several years",
            # Частота - регулярная
            r"всегда|никогда|иногда|часто|редко|обычно|постоянно|периодически",
            r"ежедневно|еженедельно|ежемесячно|ежегодно|регулярно|систематически",
            r"время от времени|изредка|крайне редко|очень часто|почти всегда",
            r"always|never|sometimes|often|rarely|usually|constantly|periodically",
            r"daily|weekly|monthly|yearly|regularly|systematically|routinely",
            r"from time to time|occasionally|very rarely|very often|almost always",
            # Частота - интенсивность
            r"каждый день|каждую неделю|каждый месяц|каждый год|каждый раз",
            r"по несколько раз в день|несколько раз в неделю|раз в месяц|раз в год",
            r"один раз|дважды|трижды|множество раз|бесчисленное количество раз",
            r"every day|every week|every month|every year|every time|each time",
            r"several times a day|several times a week|once a month|once a year",
            r"once|twice|three times|many times|countless times|numerous times",
            # Последовательность - порядок
            r"сначала|сперва|в первую очередь|прежде всего|для начала",
            r"затем|потом|после этого|далее|следом|вслед за этим",
            r"в конце|в итоге|в заключение|наконец|в конце концов|окончательно",
            r"first|firstly|initially|at first|to begin with|in the beginning",
            r"then|next|after that|afterwards|subsequently|following that",
            r"finally|lastly|in the end|ultimately|eventually|at last",
            # Последовательность - связи
            r"до этого|перед этим|накануне|заранее|предварительно|заблаговременно",
            r"после этого|вслед за этим|в результате|как следствие|впоследствии",
            r"одновременно|параллельно|в то же время|тем временем|между тем",
            r"before this|prior to this|beforehand|in advance|previously|earlier",
            r"after this|following this|as a result|consequently|subsequently",
            r"simultaneously|at the same time|meanwhile|in the meantime|concurrently",
            # Продолжительность процессов
            r"в течение|на протяжении|в ходе|в процессе|во время|при",
            r"с начала до конца|от начала и до конца|весь период|всё время",
            r"временно|постоянно|навсегда|навечно|на время|на постоянной основе",
            r"during|throughout|in the course of|in the process of|while|when",
            r"from start to finish|from beginning to end|the whole period|all the time",
            r"temporarily|permanently|forever|for good|for a while|on a permanent basis",
            # Неопределенное время
            r"когда-то|как-то раз|однажды|в какой-то момент|в определенный момент",
            r"рано или поздно|тем или иным образом|в свое время|в нужный момент",
            r"в любое время|в любой момент|когда угодно|как только|сразу как",
            r"sometime|once|at some point|at a certain moment|at some moment",
            r"sooner or later|one way or another|in due time|at the right moment",
            r"anytime|at any moment|whenever|as soon as|right when|the moment",
            # Срочность и немедленность
            r"немедленно|сразу|тотчас|мгновенно|незамедлительно|без промедления",
            r"как можно скорее|в кратчайшие сроки|в ближайшее время|в срочном порядке",
            r"не откладывая|без задержек|прямо сейчас|в эту же секунду|моментально",
            r"immediately|right away|instantly|at once|without delay|promptly",
            r"as soon as possible|in the shortest time|in the near future|urgently",
            r"without postponing|without delays|right now|this very second|momentarily"
        ],
        "importance_high": [
            # Критичность и срочность - русские
            "важно", "срочно", "критично", "критически", "немедленно", "экстренно",
            "жизненно важно", "крайне важно", "первостепенно", "приоритетно",
            "неотложно", "безотлагательно", "незамедлительно", "без промедления",
            "горит", "пожар", "тушить пожар", "горящие сроки", "дедлайн",
            # Проблемы и сбои - русские
            "проблема", "ошибка", "сбой", "авария", "катастрофа", "крах", "провал",
            "не работает", "сломалось", "отказало", "вышло из строя", "полетело",
            "глюк", "баг", "дефект", "неисправность", "поломка", "отказ системы",
            "системная ошибка", "критическая ошибка", "фатальная ошибка",
            "падение системы", "зависание", "тормозит", "лагает", "фризит",
            # Призывы о помощи - русские
            "помогите", "SOS", "тревога", "паника", "спасите", "выручайте",
            "нужна помощь", "требует внимания", "требует вмешательства",
            "необходимо решение", "нужно срочно", "горящий вопрос",
            "критическая ситуация", "чрезвычайная ситуация", "форс-мажор",
            # Безопасность и риски - русские
            "опасно", "риск", "угроза", "уязвимость", "брешь в безопасности",
            "взлом", "атака", "вирус", "заражение", "утечка данных",
            "потеря данных", "компрометация", "нарушение безопасности",
            "подозрительная активность", "несанкционированный доступ",
            # Финансовые потери - русские
            "убытки", "потери", "ущерб", "штраф", "пени", "неустойка",
            "дорого", "дорогостоящий", "затратно", "бюджет превышен",
            "перерасход", "лишние расходы", "финансовые проблемы",
            # Критичность и срочность - английские
            "urgent", "critical", "emergency", "immediate", "asap", "ASAP",
            "important", "priority", "high priority", "crucial", "vital",
            "pressing", "time-sensitive", "deadline", "overdue", "rush",
            "fire", "firefighting", "burning", "hot", "red alert",
            # Проблемы и сбои - английские
            "error", "bug", "crash", "failure", "broken", "failed", "down",
            "not working", "offline", "outage", "malfunction", "defect",
            "system failure", "critical error", "fatal error", "exception",
            "system crash", "freeze", "hang", "lag", "slow", "stuck",
            "corrupted", "damaged", "compromised", "infected", "virus",
            # Призывы о помощи - английские
            "help", "assistance", "support needed", "issue", "trouble",
            "SOS", "emergency", "panic", "crisis", "disaster", "catastrophe",
            "needs attention", "requires intervention", "action needed",
            "critical situation", "emergency situation", "force majeure",
            # Безопасность и риски - английские
            "dangerous", "risk", "threat", "vulnerability", "security breach",
            "hack", "attack", "virus", "infection", "data leak", "data loss",
            "compromise", "security violation", "suspicious activity",
            "unauthorized access", "intrusion", "breach", "exploit",
            # Финансовые потери - английские
            "loss", "damage", "fine", "penalty", "expensive", "costly",
            "budget exceeded", "overspent", "financial loss", "money lost",
            "waste", "wasteful", "overrun", "extra cost", "additional cost",
            # Решения и результаты - русские расширенные
            "решение", "вывод", "итог", "результат", "заключение", "финал",
            "окончательное решение", "ключевое решение", "стратегическое решение",
            "прорыв", "открытие", "находка", "успех", "достижение", "победа",
            "завершение", "финиш", "конец", "итоговый результат",
            "главный вывод", "основной результат", "ключевой момент",
            # Решения и результаты - английские расширенные
            "solution", "conclusion", "result", "outcome", "summary", "final",
            "final decision", "key decision", "strategic decision", "breakthrough",
            "discovery", "finding", "success", "achievement", "victory", "win",
            "completion", "finish", "end", "final result", "main conclusion",
            "key result", "key point", "milestone", "deliverable", "output",
            # Управленческие решения - русские
            "принято решение", "утверждено", "одобрено", "подписано", "согласовано",
            "директива", "приказ", "распоряжение", "указание", "постановление",
            "резолюция", "вердикт", "приговор", "судьбоносное решение",
            # Управленческие решения - английские
            "decision made", "approved", "signed", "agreed", "confirmed",
            "directive", "order", "instruction", "mandate", "resolution",
            "verdict", "ruling", "judgment", "decree", "policy change",
            # Изменения и обновления - русские
            "изменение", "обновление", "модификация", "улучшение", "оптимизация",
            "новая версия", "релиз", "выпуск", "запуск", "внедрение", "развертывание",
            "миграция", "переход", "трансформация", "реорганизация", "реструктуризация",
            # Изменения и обновления - английские
            "change", "update", "modification", "improvement", "optimization",
            "new version", "release", "launch", "deployment", "implementation",
            "migration", "transition", "transformation", "reorganization",
            "restructuring", "upgrade", "enhancement", "rollout"
        ],
        "importance_medium": [
            # Вопросы на русском
            "вопрос", "как", "почему", "что", "когда", "где", "кто",
            "можно", "нужно", "хочу", "планирую", "думаю", "считаю",
            "интересно", "любопытно", "хотелось бы знать",
            "не понимаю", "объясни", "расскажи", "покажи",
            # Вопросы на английском
            "question", "how", "why", "what", "when", "where", "who",
            "can", "should", "want", "plan", "think", "believe",
            "interesting", "curious", "would like to know",
            "don't understand", "explain", "tell", "show",
            # Планы и намерения
            "планы", "цели", "задачи", "намерения", "идеи",
            "plans", "goals", "tasks", "intentions", "ideas",
            # Мнения
            "мнение", "точка зрения", "взгляд", "позиция",
            "opinion", "point of view", "perspective", "stance"
        ],
        "context_shift": [
            # Переходы и контрасты на русском
            r"но\s+(?:сейчас|теперь|давайте|все же|тем не менее)",
            r"однако|тем не менее|все же|все-таки|впрочем",
            r"с другой стороны|с одной стороны|между тем",
            r"возвращаясь к|что касается|относительно",
            r"кстати говоря|к слову|между прочим",
            r"в то же время|одновременно|параллельно",
            # Переходы на английском
            r"however|but now|nevertheless|nonetheless|still",
            r"on the other hand|on one hand|meanwhile",
            r"getting back to|regarding|concerning|about",
            r"speaking of|by the way|incidentally",
            r"at the same time|simultaneously|meanwhile",
            # Логические связки
            r"поэтому|следовательно|таким образом|итак",
            r"therefore|thus|consequently|so|hence",
            r"кроме того|более того|к тому же|также",
            r"moreover|furthermore|in addition|also|besides"
        ],
        "technical_context": [
            # Программирование
            r"код|code|программа|program|скрипт|script|алгоритм|algorithm",
            r"функция|function|метод|method|класс|class|объект|object",
            r"переменная|variable|константа|constant|массив|array",
            r"цикл|loop|условие|condition|if|else|switch|case",
            # Ошибки и отладка
            r"ошибка|error|баг|bug|исключение|exception|сбой|crash",
            r"отладка|debug|debugging|тест|test|тестирование|testing",
            r"логи|logs|трассировка|trace|stacktrace|backtrace",
            # Базы данных
            r"база данных|database|БД|DB|SQL|запрос|query|таблица|table",
            r"индекс|index|ключ|key|связь|relation|транзакция|transaction",
            r"миграция|migration|схема|schema|модель|model",
            # Веб-разработка
            r"API|REST|GraphQL|endpoint|микросервис|microservice",
            r"HTTP|HTTPS|GET|POST|PUT|DELETE|PATCH|статус код|status code",
            r"JSON|XML|YAML|HTML|CSS|JavaScript|TypeScript",
            # Инфраструктура
            r"сервер|server|клиент|client|frontend|backend|fullstack",
            r"docker|kubernetes|контейнер|container|деплой|deploy",
            r"CI/CD|DevOps|мониторинг|monitoring|логирование|logging",
            r"облако|cloud|AWS|Azure|GCP|хостинг|hosting"
        ],
        "emotional_context": [
            # Позитивные эмоции на русском
            r"нравится|люблю|обожаю|восхищен|радуюсь|счастлив",
            r"хорошо|отлично|замечательно|прекрасно|великолепно|супер",
            r"доволен|удовлетворен|приятно|радостно|весело",
            r"спасибо|благодарю|признателен|благодарен",
            # Позитивные эмоции на английском
            r"like|love|adore|amazed|happy|joyful|pleased",
            r"good|great|excellent|wonderful|awesome|fantastic",
            r"satisfied|content|pleasant|cheerful|delighted",
            r"thanks|thank you|grateful|appreciate|thankful",
            # Негативные эмоции на русском
            r"не нравится|ненавижу|расстроен|грустно|печально",
            r"плохо|ужасно|отвратительно|кошмар|катастрофа",
            r"злой|сердитый|раздражен|недоволен|возмущен",
            r"разочарован|огорчен|подавлен|депрессия",
            # Негативные эмоции на английском
            r"dislike|hate|upset|sad|disappointed|frustrated",
            r"bad|terrible|awful|horrible|disgusting|nightmare",
            r"angry|mad|irritated|annoyed|furious|outraged",
            r"disappointed|discouraged|depressed|down",
            # Нейтральные состояния
            r"нормально|так себе|средне|обычно|привычно",
            r"okay|fine|average|normal|usual|typical",
            r"не знаю|сомневаюсь|не уверен|может быть",
            r"don't know|doubt|not sure|maybe|perhaps|possibly"
        ],
        "dialogue": {
            "question_answer": r"(.*?)(?:пользователь:|user:|вопрос:|question:)(.*?)(?:ответ:|answer:|assistant:|агент:)(.*?)(?=пользователь:|user:|$)",
            "topic_discussion": r"(.*?)(?:говорили о|обсуждали|про|about)(.*?)(?=\.|!|\?|$)",
            "problem_solution": r"(.*?)(?:проблема|ошибка|не работает|problem|error)(.*?)(?:решение|исправить|fix|solution)(.*?)(?=\.|!|\?|$)",
            "instruction": r"(.*?)(?:как|how to|инструкция|instruction)(.*?)(?=\.|!|\?|$)",
            "explanation": r"(.*?)(?:объясни|explain|расскажи|tell me)(.*?)(?=\.|!|\?|$)"
        }
    }


def get_comprehensive_user_modes() -> dict:
    """Возвращает максимально полный набор пользовательских режимов"""
    return {
        "casual": {
            "chunking_strategy": "size_based",
            "max_chunk_size": 256,
            "max_context_length": 1000,
            "importance_threshold": 0.3,
            "retrieval_k": 6,
            "final_k": 3,
            "description": "Быстрые короткие ответы для повседневного общения"
        },
        "detailed": {
            "chunking_strategy": "hybrid",
            "max_chunk_size": 512,
            "max_context_length": 2000,
            "importance_threshold": 0.5,
            "retrieval_k": 8,
            "final_k": 4,
            "description": "Сбалансированный режим для подробного общения"
        },
        "technical": {
            "chunking_strategy": "topic_based",
            "max_chunk_size": 768,
            "max_context_length": 3000,
            "importance_threshold": 0.7,
            "retrieval_k": 10,
            "final_k": 5,
            "description": "Технический режим с фокусом на код и алгоритмы"
        },
        "research": {
            "chunking_strategy": "importance_based",
            "max_chunk_size": 1024,
            "max_context_length": 4000,
            "importance_threshold": 0.8,
            "retrieval_k": 12,
            "final_k": 6,
            "description": "Исследовательский режим для глубокого анализа"
        },
        "creative": {
            "chunking_strategy": "context_based",
            "max_chunk_size": 600,
            "max_context_length": 2500,
            "importance_threshold": 0.4,
            "retrieval_k": 10,
            "final_k": 5,
            "description": "Креативный режим для генерации идей и контента"
        },
        "support": {
            "chunking_strategy": "emotional_context",
            "max_chunk_size": 400,
            "max_context_length": 1500,
            "importance_threshold": 0.6,
            "retrieval_k": 8,
            "final_k": 4,
            "description": "Режим поддержки с фокусом на эмоциональный контекст"
        },
        "learning": {
            "chunking_strategy": "hybrid",
            "max_chunk_size": 700,
            "max_context_length": 3500,
            "importance_threshold": 0.6,
            "retrieval_k": 15,
            "final_k": 7,
            "description": "Обучающий режим для изучения новых тем"
        },
        "expert": {
            "chunking_strategy": "importance_based",
            "max_chunk_size": 1200,
            "max_context_length": 5000,
            "importance_threshold": 0.9,
            "retrieval_k": 20,
            "final_k": 10,
            "description": "Экспертный режим с максимальным контекстом"
        },
        "quick": {
            "chunking_strategy": "size_based",
            "max_chunk_size": 200,
            "max_context_length": 800,
            "importance_threshold": 0.2,
            "retrieval_k": 4,
            "final_k": 2,
            "description": "Быстрый режим для коротких ответов"
        },
        "comprehensive": {
            "chunking_strategy": "hybrid",
            "max_chunk_size": 1500,
            "max_context_length": 6000,
            "importance_threshold": 0.8,
            "retrieval_k": 25,
            "final_k": 12,
            "description": "Максимально полный режим с богатым контекстом"
        }
    }


def create_summarization_settings_table():
    """Создает таблицу настроек суммаризации"""
    try:
        # Получаем URL базы данных
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Создаем таблицу
        logger.info("Creating agent_summarization_settings table...")
        AgentSummarizationSettings.__table__.create(engine, checkfirst=True)
        
        logger.info("✅ Table agent_summarization_settings created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating summarization settings table: {e}")
        return False


def create_default_settings():
    """Создает настройки по умолчанию для существующих агентов"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Получаем список существующих агентов
        result = session.execute(text("SELECT DISTINCT name FROM agent_profiles"))
        agent_names = [row[0] for row in result]
        
        if not agent_names:
            logger.info("No existing agents found, skipping default settings creation")
            return True
        
        logger.info(f"Creating default settings for {len(agent_names)} agents...")
        
        for agent in agents:
            # Проверяем, нет ли уже настроек для этого агента
            existing = session.query(AgentSummarizationSettings).filter(
                AgentSummarizationSettings.agent_name == agent.name
            ).first()
            
            if existing:
                logger.info(f"Settings for agent '{agent.name}' already exist, skipping")
                continue
            
            # Создаем специализированные настройки в зависимости от роли агента
            agent_config = get_specialized_config_for_agent(agent.name, agent.role if hasattr(agent, 'role') else 'universal')
            
            settings = AgentSummarizationSettings.from_config_dict(agent.name, agent_config)
            session.add(settings)
            
            logger.info(f"✅ Created default settings for agent: {agent.name}")
        
        session.commit()
        session.close()
        
        logger.info(f"✅ Successfully created default settings for {len(agents)} agents")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating default settings: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def verify_migration():
    """Проверяет успешность миграции"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Проверяем наличие таблицы
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'agent_summarization_settings'
        """))
        
        table_exists = result.scalar() > 0
        
        if not table_exists:
            logger.error("❌ Table agent_summarization_settings not found")
            return False
        
        # Проверяем количество записей
        count = session.query(AgentSummarizationSettings).count()
        logger.info(f"✅ Table exists with {count} settings records")
        
        # Проверяем структуру таблицы
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'agent_summarization_settings'
            ORDER BY ordinal_position
        """))
        
        columns = [row[0] for row in result]
        expected_columns = [
            'id', 'agent_name', 'enabled', 'chunking_strategy', 
            'max_chunk_size', 'min_chunk_size', 'overlap_size',
            'max_context_length', 'retrieval_k', 'final_k',
            'high_importance_threshold', 'medium_importance_threshold',
            'min_relevance_score', 'time_gap_threshold',
            'ranking_weights', 'temporal_weights', 'importance_weights',
            'topic_shift_patterns', 'question_patterns', 'completion_patterns',
            'temporal_absolute_markers', 'temporal_relative_markers',
            'high_importance_keywords', 'medium_importance_keywords',
            'context_shift_markers', 'technical_context_markers',
            'emotional_context_markers', 'dialogue_patterns',
            'user_modes', 'created_at', 'updated_at', 'version'
        ]
        
        missing_columns = set(expected_columns) - set(columns)
        if missing_columns:
            logger.warning(f"⚠️  Missing columns: {missing_columns}")
        else:
            logger.info("✅ All expected columns present")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")
        return False


def main():
    """Основная функция миграции"""
    logger.info("🚀 Starting summarization settings migration...")
    
    # Шаг 1: Создание таблицы
    if not create_summarization_settings_table():
        logger.error("❌ Migration failed at table creation step")
        return False
    
    # Шаг 2: Создание настроек по умолчанию
    if not create_default_settings():
        logger.error("❌ Migration failed at default settings creation step")
        return False
    
    # Шаг 3: Проверка миграции
    if not verify_migration():
        logger.error("❌ Migration verification failed")
        return False
    
    logger.info("🎉 Summarization settings migration completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
