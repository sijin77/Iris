# TODO (tools:add_trigger):
# - Поддержка non-interactive режима и флагов CLI
# - Валидация/нормализация входа, локализация сообщений
# - Команда для списка/удаления/экспорта триггеров
# - Тесты CLI
from agent.models import SessionLocal, add_trigger, TriggerType

def add_trigger_interactive():
    print("Добавление нового триггера.")
    print("Выберите тип триггера:")
    for idx, t in enumerate(TriggerType):
        print(f"{idx+1}. {t.value}")
    type_idx = int(input("Введите номер типа: ")) - 1
    trigger_type = list(TriggerType)[type_idx]
    phrase = input("Введите текст триггера: ").strip()
    if not phrase:
        print("Текст триггера не может быть пустым!")
        return
    with SessionLocal() as session:
        success = add_trigger(session, phrase, trigger_type)
        if success:
            print(f"Триггер '{phrase}' (тип: {trigger_type.value}) успешно добавлен!")
        else:
            print(f"Триггер '{phrase}' (тип: {trigger_type.value}) уже существует.") 