import json
from pathlib import Path


# Загружаем настройки агента из agent_config.json
CONFIG_PATH = Path(__file__).with_name("agent_config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


LANGUAGE = CONFIG.get("language", "ru")
SEARCH_LANGUAGES = CONFIG.get("search_languages", ["ru"])
EXCLUDE_LANGUAGES = CONFIG.get("exclude_languages", [])

TASK_TYPE = CONFIG.get("task_type", "ремонтные и бытовые работы")

EXCLUDED_KEYWORDS = [
    word.lower()
    for word in CONFIG.get("exclude", [])
]

INCLUDED_KEYWORDS = [
    word.lower()
    for word in CONFIG.get("include", [])
]


def is_russian_text(text):
    """Проверяет, содержит ли объявление русский текст."""
    if not text:
        return False

    russian_letters = (
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    )

    text = text.lower()

    russian_count = sum(
        1 for char in text
        if char in russian_letters
    )

    return russian_count >= 5


def is_repair_request(text):
    """Проверяет, подходит ли объявление под нашу задачу."""
    if not text:
        return False

    text_lower = text.lower()

    # Только русский язык
    if LANGUAGE == "ru" and not is_russian_text(text):
        return False

    # Исключаем вакансии, резюме, рекламу и т.д.
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in text_lower:
            return False

    # Должно быть хотя бы одно ключевое слово
    return any(
        keyword in text_lower
        for keyword in INCLUDED_KEYWORDS
    )


def analyze_ad(text):
    """Анализирует объявление."""
    if is_repair_request(text):
        return {
            "match": True,
            "text": text,
            "reason": (
                "Объявление похоже на заявку клиента "
                "на ремонтные или бытовые работы."
            )
        }

    return {
        "match": False,
        "text": text,
        "reason": "Объявление не соответствует заданным критериям."
    }


if __name__ == "__main__":
    print("ИИ-агент для поиска объявлений о ремонтных и бытовых работах")
    print("Язык поиска:", SEARCH_LANGUAGES)
    print("Исключённые языки:", EXCLUDE_LANGUAGES)
    print("Тип задач:", TASK_TYPE)
    print("Конфигурация загружена из agent_config.json")
