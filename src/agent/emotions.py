# TODO (emotions):
# - Подключить модельный анализ тональности/эмоций (ru/xx), fallback на правила
# - Нормализация и поддержка нескольких языков
# - Интенсивность эмоций, нейтрал/сарказм/ирония
# - Тесты и метрики качества

def analyze_emotion(text: str) -> str:
	positive_words = {"счастлив", "рад", "отлично", "классно", "супер", "улыбка", "люблю", "благодарен", "вдохновлён", "восхищён", "прекрасно", "замечательно", "улыбаюсь", "ура"}
	negative_words = {"грусть", "печаль", "плохо", "разочарован", "устал", "одиноко", "тоска", "грустно", "разбит", "огорчён", "разочарование", "потеря", "плач", "слёзы", "тревога", "боль"}
	anger_words = {"злюсь", "злость", "раздражён", "бесит", "ненавижу", "ярость", "раздражение", "злой", "агрессия", "бешенство", "взбешён"}
	text_lower = text.lower()
	if any(word in text_lower for word in anger_words):
		return "anger"
	if any(word in text_lower for word in negative_words):
		return "negative"
	if any(word in text_lower for word in positive_words):
		return "positive"
	return "neutral" 