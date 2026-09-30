import json
from pathlib import Path
import requests


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


# Признаки вакансии / поиска работника.
# Они помогают отличить заявку клиента от объявления работодателя.
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

    # Явные признаки вакансии
    for marker in VACANCY_MARKERS:
        if marker in text_lower:
            return True

    # "Требуется + профессия" само по себе не является вакансией:
    # это может быть заявка клиента на мастера.
    # Поэтому слово "требуется" без других признаков не исключаем.

    return False


def is_repair_request(text):
    if not text:
        return False

    text_lower = text.lower()

    # Работаем только с русскоязычными объявлениями
    if LANGUAGE == "ru" and not is_russian_text(text):
        return False

    # Исключаем явные нежелательные типы объявлений
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in text_lower:
            return False

    # Исключаем вакансии работодателей
    if is_vacancy(text):
        return False

    # Должно присутствовать хотя бы одно слово,
    # связанное с ремонтом или бытовой работой
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


if __name__ == "__main__":
    print("=== ИИ-агент поиска объявлений ===")
    print(f"Язык: {LANGUAGE}")
    print(f"Языки поиска: {', '.join(SEARCH_LANGUAGES)}")
    print(
        f"Исключённые языки: "
        f"{', '.join(EXCLUDE_LANGUAGES) if EXCLUDE_LANGUAGES else 'нет'}"
    )
    print(f"Тип задач: {TASK_TYPE}")
    print("Конфигурация загружена из agent_config.json")
