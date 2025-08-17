"""
Миграция для создания расширенных таблиц эмоциональной памяти и персистентности профилей.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from agent.models import Base, engine
from agent.models_extended import *  # Импортируем все новые модели

def create_extended_tables():
    """Создает все расширенные таблицы"""
    try:
        print("🔄 Создание расширенных таблиц...")
        
        # Создаем все таблицы, определенные в моделях
        Base.metadata.create_all(bind=engine)
        
        print("✅ Расширенные таблицы успешно созданы:")
        print("   - profile_changes (история изменений профилей)")
        print("   - profile_snapshots (снимки состояния профилей)")
        print("   - emotional_fragments (эмоциональные фрагменты)")
        print("   - emotional_states (эмоциональные состояния)")
        print("   - feedback_analysis (анализ обратной связи)")
        print("   - memory_fragments (фрагменты памяти L2)")
        print("   - memory_operation_logs (логи операций памяти)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def check_tables_exist():
    """Проверяет, существуют ли таблицы"""
    try:
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        expected_tables = [
            'profile_changes',
            'profile_snapshots', 
            'emotional_fragments',
            'emotional_states',
            'feedback_analysis',
            'memory_fragments',
            'memory_operation_logs'
        ]
        
        print("📋 Проверка существующих таблиц:")
        for table in expected_tables:
            exists = table in existing_tables
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
        
        missing_tables = [table for table in expected_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"\n⚠️  Отсутствующие таблицы: {', '.join(missing_tables)}")
            return False
        else:
            print("\n🎉 Все таблицы существуют!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Миграция расширенных таблиц для эмоциональной памяти")
    print("=" * 60)
    
    # Сначала проверяем текущее состояние
    print("1️⃣ Проверка текущего состояния БД:")
    tables_exist = check_tables_exist()
    
    if not tables_exist:
        print("\n2️⃣ Создание недостающих таблиц:")
        success = create_extended_tables()
        
        if success:
            print("\n3️⃣ Повторная проверка:")
            check_tables_exist()
            print("\n🎊 Миграция завершена успешно!")
        else:
            print("\n💥 Миграция не удалась!")
            sys.exit(1)
    else:
        print("\n✨ Все таблицы уже существуют, миграция не требуется!")
