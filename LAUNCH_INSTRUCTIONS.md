# 🚀 Инструкции по запуску Iriska v2.0

## 🎉 **Система готова к запуску!**

Iriska теперь включает:
- 🧠 **Эмоциональную память** с автоматической адаптацией
- 💾 **Многоуровневую архитектуру памяти** L1-L4
- 🔄 **Персистентное хранение** профилей в БД
- 📊 **Полный API** для управления и мониторинга

## 📋 **Пошаговый запуск**

### **1. Подготовка базы данных**

```bash
# Создаем новые таблицы для эмоциональной памяти и персистентности
cd src
python migrations/create_extended_tables.py
```

Ожидаемый вывод:
```
🚀 Миграция расширенных таблиц для эмоциональной памяти
============================================================
1️⃣ Проверка текущего состояния БД:
   ✅ profile_changes
   ✅ profile_snapshots
   ✅ emotional_fragments
   ✅ emotional_states
   ✅ feedback_analysis
   ✅ memory_fragments
   ✅ memory_operation_logs

🎊 Миграция завершена успешно!
```

### **2. Запуск инфраструктуры**

```bash
# Запускаем Redis и ChromaDB через Docker
docker-compose up -d redis chromadb

# Проверяем статус
docker-compose ps
```

### **3. Запуск Iriska с полной системой памяти**

```bash
# Основной запуск с новой системой
cd src
python main_with_memory.py
```

Ожидаемый вывод:
```
🚀 Запуск Iriska с полной системой памяти...
✅ Расширенный контроллер памяти инициализирован
✅ Эмоциональная память инициализирована
✅ Фоновые процессы памяти запущены
🎉 Iriska полностью инициализирована!
```

### **4. Проверка работоспособности**

Откройте браузер: http://localhost:8000

**Ключевые endpoints для проверки:**

```bash
# Основная информация
curl http://localhost:8000/

# Статус системы памяти
curl http://localhost:8000/api/v1/memory/status

# Статус эмоциональной памяти
curl http://localhost:8000/api/v1/emotional/status

# Здоровье системы управления профилями
curl http://localhost:8000/api/v1/profiles/health
```

## 🧪 **Тестирование функциональности**

### **Тест эмоциональной системы:**
```bash
cd src
python test_emotional_system.py
```

### **Тест системы памяти:**
```bash
python test_storage_integration.py
```

### **Интерактивный тест через API:**

```bash
# 1. Отправляем сообщение с эмоциональной обратной связью
curl -X POST http://localhost:8000/api/v1/feedback/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "feedback_text": "Мне нравится, как ты объясняешь, но будь менее формальным",
    "agent_name": "iriska"
  }'

# 2. Проверяем, что изменения сохранились
curl http://localhost:8000/api/v1/profiles/iriska/changes?user_id=test_user

# 3. Смотрим эмоциональную сводку
curl http://localhost:8000/api/v1/emotional/summary/test_user?hours=1
```

## 📊 **Мониторинг и управление**

### **Веб-интерфейс:**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### **Основные API endpoints:**

#### **Управление памятью:**
- `GET /api/v1/memory/status` - статус системы памяти
- `POST /api/v1/memory/optimize` - запуск оптимизации
- `POST /api/v1/memory/emergency` - экстренная очистка

#### **Эмоциональная память:**
- `GET /api/v1/emotional/status` - статус эмоциональной системы
- `GET /api/v1/emotional/summary/{user_id}` - эмоциональная сводка

#### **Управление профилями:**
- `GET /api/v1/profiles/{agent}/changes` - история изменений
- `POST /api/v1/profiles/snapshots/create` - создать снимок
- `POST /api/v1/profiles/rollback` - откат изменений
- `GET /api/v1/profiles/{agent}/evolution` - анализ эволюции

#### **Обратная связь:**
- `POST /api/v1/feedback/process` - обработка обратной связи
- `GET /api/v1/feedback/pending-changes` - ожидающие изменения
- `GET /api/v1/feedback/effectiveness/{agent}` - анализ эффективности

## 🎯 **Примеры использования**

### **Сценарий 1: Пользователь дает обратную связь**

```javascript
// Пользователь: "Ты слишком формальный, будь дружелюбнее"
fetch('/api/v1/feedback/process', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    feedback_text: 'Ты слишком формальный, будь дружелюбнее',
    agent_name: 'iriska'
  })
})
.then(r => r.json())
.then(data => console.log('Обратная связь обработана:', data));
```

**Результат:**
- Эмоция: `constructive_feedback`
- Изменение: `tone: "professional" → "friendly"`
- Сохранение в БД с возможностью отката

### **Сценарий 2: Анализ эволюции профиля**

```bash
curl http://localhost:8000/api/v1/profiles/iriska/evolution?days_back=7
```

**Получите:**
- Статистику изменений за неделю
- Анализ по типам эмоций
- Рекомендации по оптимизации

### **Сценарий 3: Откат нежелательных изменений**

```bash
# Откат изменений за последние 2 часа
curl -X POST http://localhost:8000/api/v1/feedback/rollback/iriska?hours_back=2
```

## ⚡ **Производительность**

### **Ожидаемые характеристики:**
- **L1 (Redis)**: < 1ms доступ к горячим данным
- **L2 (SQLite)**: < 10ms доступ к теплым данным  
- **L3 (ChromaDB)**: < 100ms семантический поиск
- **Эмоциональный анализ**: < 50ms на сообщение
- **Автоматическая корректировка**: < 200ms полный цикл

### **Автоматическая оптимизация:**
- Каждые 30 минут: продвижение/понижение данных
- Каждый час: очистка устаревших данных
- Ежедневно: создание снимков профилей
- При переполнении: экстренная очистка

## 🛡️ **Безопасность и надежность**

### **Автоматические резервные копии:**
- Снимки профилей перед каждым изменением
- Ежедневные резервные копии
- История всех изменений в БД

### **Защита от ошибок:**
- Валидация всех изменений профилей
- Пороги уверенности для автоприменения
- Лимиты на количество изменений в день
- Возможность отката к любому состоянию

## 🔧 **Настройка**

### **Конфигурация памяти** (`MemoryConfig`):
```python
memory_config = MemoryConfig(
    optimization_interval_minutes=30,  # Интервал оптимизации
    cleanup_interval_minutes=60,       # Интервал очистки
    max_fragments_per_level=10000,     # Максимум фрагментов на уровень
    promotion_threshold=0.7,           # Порог продвижения
    demotion_threshold=0.3,            # Порог понижения
    eviction_threshold=0.1             # Порог удаления
)
```

### **Конфигурация эмоциональной памяти** (`EmotionalMemoryConfig`):
```python
emotional_config = EmotionalMemoryConfig(
    emotion_detection_threshold=0.3,     # Порог обнаружения эмоций
    emotional_weight_multiplier=1.5,     # Множитель эмоционального веса
    profile_adjustment_threshold=0.7,    # Порог автоприменения изменений
    max_adjustments_per_day=3           # Максимум корректировок в день
)
```

## 🎊 **Поздравляем!**

**Iriska v2.0 успешно запущена!** 

Теперь у вас есть:
- 🧠 Эмоционально интеллектуальный агент
- 💾 Автоматическая система управления памятью
- 🔄 Самообучающийся профиль
- 📊 Полная наблюдаемость и контроль

**Система готова к продакшену и реальному использованию!** 🚀

---

*Для поддержки и вопросов обращайтесь к документации в `.cursor-memory/technical/`*
