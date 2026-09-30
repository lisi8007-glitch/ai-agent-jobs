import json
import os
import requests
from pathlib import Path


# Загружаем настройки агента
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


# Признаки вакансии работодателя
VACANCY_MARKERS = [
    "вакансия",
    "вакансии",
    "ищем сотрудника",
    "ищем работника",
    "требуется сотрудник",
    "требуется работник",
    "работа официальная",
    "официальное трудоустройство",
    "трудоустройство",
    "график работы",
    "заработная плата",
    "зарплата",
    "оклад",
    "предоставляется жильё",
    "предоставляется жилье",
    "жильё предоставляется",
    "жилье предоставляется",
]


def is_russian_text(text):
    if not text:
        return False

    russian_letters = (
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    )

    text_lower = text.lower()

    russian_count = sum(
        1 for char in text_lower
        if char in russian_letters
    )

    return russian_count >= 5


def is_vacancy(text):
    if not text:
        return False

    text_lower = text.lower()

    for marker in VACANCY_MARKERS:
        if marker in text_lower:
            return True

    return False


def is_repair_request(text):
    if not text:
        return False

    text_lower = text.lower()

    # Только русскоязычные объявления
    if LANGUAGE == "ru" and not is_russian_text(text):
        return False

    # Исключаем нежелательные объявления
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in text_lower:
            return False

    # Исключаем вакансии работодателей
    if is_vacancy(text):
        return False

    # Ищем слова, связанные с ремонтом
    return any(
        keyword in text_lower
        for keyword in INCLUDED_KEYWORDS
    )


def analyze_ad(text):
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
        "reason": (
            "Объявление не соответствует заданным критериям."
        )
    }


def search_web(query):
    """
    Поиск объявлений через TinyFish Search.
    API-ключ берётся из GitHub Secret TINYFISH_API_KEY.
    """

    api_key = os.environ.get("TINYFISH_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Не найден секрет TINYFISH_API_KEY"
        )

    response = requests.get(
        "https://api.search.tinyfish.ai",
        headers={
            "X-API-Key": api_key
        },
        params={
            "query": query,
            "language": "ru"
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    print("=== ИИ-агент поиска объявлений ===")
    print(f"Язык: {LANGUAGE}")
    print(
        f"Языки поиска: "
        f"{', '.join(SEARCH_LANGUAGES)}"
    )
    print(
        f"Исключённые языки: "
        f"{', '.join(EXCLUDE_LANGUAGES) if EXCLUDE_LANGUAGES else 'нет'}"
    )
    print(f"Тип задач: {TASK_TYPE}")
    print("Конфигурация загружена из agent_config.json")
