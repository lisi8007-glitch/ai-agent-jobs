# ИИ-агент для поиска объявлений о ремонтных и бытовых работах
# Язык объявлений: только русский

RUSSIAN_KEYWORDS = [
    "ремонт",
    "сантехник",
    "сантехника",
    "электрик",
    "электрика",
    "монтаж",
    "установка",
    "мастер",
    "строитель",
    "плитка",
    "плиточник",
    "отделка",
    "штукатурка",
    "маляр",
    "гипсокартон",
    "водопровод",
    "отопление",
    "бойлер",
    "кондиционер",
]

EXCLUDED_KEYWORDS = [
    "вакансия",
    "вакансии",
    "ищу работу",
    "резюме",
    "предлагаю услуги",
    "оказываю услуги",
    "реклама",
]

def is_russian_text(text):
    """Проверяет, содержит ли объявление русский текст."""
    russian_letters = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    text = text.lower()

    if not text:
        return False

    russian_count = sum(1 for char in text if char in russian_letters)
    return russian_count >= 5


def is_repair_request(text):
    """Определяет, похоже ли объявление на заявку клиента."""
    text_lower = text.lower()

    if not is_russian_text(text):
        return False

    for keyword in EXCLUDED_KEYWORDS:
        if keyword in text_lower:
            return False

    return any(keyword in text_lower for keyword in RUSSIAN_KEYWORDS)


def analyze_ad(text):
    """Анализирует объявление."""
    if is_repair_request(text):
        return {
            "match": True,
            "text": text,
            "reason": "Объявление похоже на заявку клиента на ремонтные или бытовые работы."
        }

    return {
        "match": False,
        "text": text,
        "reason": "Объявление не соответствует заданным критериям."
    }


if __name__ == "__main__":
    print("ИИ-агент для поиска заявок на ремонтные и бытовые работы")
    print("Поиск и анализ: только русскоязычные объявления.")
