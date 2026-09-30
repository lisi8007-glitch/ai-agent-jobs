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
TASK_TYPE = CONFIG.get(
    "task_type",
    "ремонтные и бытовые работы"
)


EXCLUDED_KEYWORDS = [
    word.lower()
    for word in CONFIG.get("exclude", [])
]

INCLUDED_KEYWORDS = [
    word.lower()
    for word in CONFIG.get("include", [])
]


# ==========================================
# Признаки вакансии работодателя
# ==========================================

VACANCY_MARKERS = [
    "вакансия",
    "вакансии",
    "ищем сотрудника",
    "ищем работника",
    "требуется сотрудник",
    "требуется работник",
    "требуется персонал",
    "нужен сотрудник",
    "нужен работник",
    "работа официальная",
    "официальное трудоустройство",
    "трудоустройство",
    "график работы",
    "сменный график",
    "смена",
    "ставка",
    "заработная плата",
    "зарплата",
    "оклад",
    "предоставляется жильё",
    "предоставляется жилье",
    "жильё предоставляется",
    "жилье предоставляется",
]


# ==========================================
# Признаки предложения услуг мастером
# ==========================================

SERVICE_OFFER_MARKERS = [
    "оказываю услуги",
    "оказываем услуги",
    "предлагаю услуги",
    "предлагаем услуги",
    "предоставляю услуги",
    "предоставляем услуги",
    "выполняю работы",
    "выполняем работы",
    "выполню работы",
    "делаю ремонт",
    "делаем ремонт",
    "ремонтируем",
    "работаю сантехником",
    "работаю электриком",
    "работаю мастером",
    "работаю плиточником",
    "работаю строителем",
    "мастер на все руки",
    "услуги мастера",
    "мои услуги",
    "наши услуги",
    "услуги от",
    "услуги с",
    "обращайтесь",
    "звоните",
    "пишите в личку",
    "пишите в лс",
    "пишите мне",
    "whatsapp:",
    "viber:",
    "telegram:",
]


# ==========================================
# Явные признаки заявки клиента
# ==========================================

CLIENT_REQUEST_MARKERS = [
    "нужен мастер",
    "нужна мастер",
    "нужен сантехник",
    "нужна сантехника",
    "нужен электрик",
    "нужен плиточник",
    "нужен строитель",
    "нужен специалист",
    "нужен человек",

    "ищу мастера",
    "ищу сантехника",
    "ищу электрика",
    "ищу плиточника",
    "ищу строителя",
    "ищу специалиста",
    "ищу человека",

    "ищем мастера",
    "ищем сантехника",
    "ищем электрика",
    "ищем специалиста",

    "кто может",
    "кто сможет",
    "кто знает мастера",
    "кто знает сантехника",
    "кто знает электрика",

    "посоветуйте мастера",
    "посоветуйте сантехника",
    "посоветуйте электрика",
    "посоветуйте плиточника",
    "посоветуйте специалиста",

    "подскажите мастера",
    "подскажите сантехника",
    "подскажите электрика",
    "подскажите плиточника",
    "подскажите специалиста",

    "требуется мастер",
    "требуется сантехник",
    "требуется электрик",
    "требуется плиточник",
    "требуется специалист",

    "нужно установить",
    "нужно заменить",
    "нужно отремонтировать",
    "нужно починить",

    "надо установить",
    "надо заменить",
    "надо отремонтировать",
    "надо починить",

    "необходимо установить",
    "необходимо заменить",
    "необходимо отремонтировать",
    "необходимо починить",

    "хочу установить",
    "хочу заменить",
    "хочу отремонтировать",

    "кто занимается",
    "кто делает",
    "кто устанавливает",
    "кто ремонтирует",

    "есть мастер",
    "есть сантехник",
    "есть электрик",
]


# ==========================================
# Признаки конкретной проблемы клиента
# ==========================================

PROBLEM_MARKERS = [
    "сломался",
    "сломалась",
    "сломалось",
    "сломались",

    "не работает",
    "не включается",
    "не выключается",
    "не греет",
    "не охлаждает",

    "течёт",
    "течет",
    "протекает",
    "капает",

    "засорился",
    "засорилась",
    "засор",
    "протечка",

    "трещина",
    "треснул",
    "треснула",

    "разбилось",
    "разбилась",
    "разбит",

    "нужна помощь",
    "помогите",
]


# ==========================================
# Проверка русского языка
# ==========================================

def is_russian_text(text):
    if not text:
        return False

    russian_letters = (
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    )

    text_lower = text.lower()

    russian_count = sum(
        1
        for char in text_lower
        if char in russian_letters
    )

    return russian_count >= 5


# ==========================================
# Проверка вакансии
# ==========================================

def is_vacancy(text):
    if not text:
        return False

    text_lower = text.lower()

    return any(
        marker in text_lower
        for marker in VACANCY_MARKERS
    )


# ==========================================
# Проверка заявки клиента
# ==========================================

def has_client_request(text):
    if not text:
        return False

    text_lower = text.lower()

    return any(
        marker in text_lower
        for marker in CLIENT_REQUEST_MARKERS
    )


# ==========================================
# Проверка проблемы
# ==========================================

def has_problem(text):
    if not text:
        return False

    text_lower = text.lower()

    return any(
        marker in text_lower
        for marker in PROBLEM_MARKERS
    )


# ==========================================
# Проверка ремонтной тематики
# ==========================================

def has_repair_topic(text):
    if not text:
        return False

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in INCLUDED_KEYWORDS
    )


# ==========================================
# Проверка предложения услуг
# ==========================================

def is_service_offer(text):
    if not text:
        return False

    text_lower = text.lower()

    # Явное предложение услуг
    if any(
        marker in text_lower
        for marker in SERVICE_OFFER_MARKERS
    ):
        return True

    # Рекламные объявления:
    # "Мастер! Электрик! Сантехник! Недорого."
    service_words = [
        "мастер",
        "электрик",
        "сантехник",
        "плиточник",
        "строитель",
        "ремонт",
    ]

    advertising_words = [
        "недорого",
        "цена",
        "цены",
        "от 20€",
        "от 20 €",
        "от 30€",
        "от 30 €",
        "доступно",
    ]

    has_service_word = any(
        word in text_lower
        for word in service_words
    )

    has_advertising_word = any(
        word in text_lower
        for word in advertising_words
    )

    return (
        has_service_word
        and has_advertising_word
    )


# ==========================================
# Основная классификация
# ==========================================

def is_repair_request(text):
    if not text:
        return False

    text_lower = text.lower()

    # Только русскоязычные объявления
    if (
        LANGUAGE == "ru"
        and not is_russian_text(text)
    ):
        return False

    # Исключаем нежелательные объявления
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in text_lower:
            return False

    # Исключаем вакансии работодателей
    if is_vacancy(text):
        return False

    # Исключаем предложения услуг мастеров
    if is_service_offer(text):
        return False

    # В тексте обязательно должна быть
    # ремонтная или бытовая тематика
    if not has_repair_topic(text):
        return False

    # Явная заявка клиента
    if has_client_request(text):
        return True

    # Описание конкретной проблемы
    if has_problem(text):
        return True

    # Просто слова "мастер", "ремонт",
    # "сантехник" и т.п. без заявки
    # клиента не принимаем.
    return False


# ==========================================
# Анализ объявления
# ==========================================

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

    if is_service_offer(text):
        reason = (
            "Объявление похоже на предложение услуг "
            "мастера, а не на заявку клиента."
        )

    elif is_vacancy(text):
        reason = (
            "Объявление похоже на вакансию "
            "работодателя."
        )

    elif (
        LANGUAGE == "ru"
        and not is_russian_text(text)
    ):
        reason = (
            "Объявление не является "
            "русскоязычным."
        )

    elif has_repair_topic(text):
        reason = (
            "Есть ремонтная тематика, но нет "
            "признаков реальной заявки клиента."
        )

    else:
        reason = (
            "Объявление не соответствует "
            "заданным критериям."
        )

    return {
        "match": False,
        "text": text,
        "reason": reason
    }


# ==========================================
# Поиск через TinyFish
# ==========================================

def search_web(query):
    """
    Поиск объявлений через TinyFish Search.
    API-ключ берётся из GitHub Secret
    TINYFISH_API_KEY.
    """

    api_key = os.environ.get(
        "TINYFISH_API_KEY"
    )

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


# ==========================================
# Запуск агента
# ==========================================

if __name__ == "__main__":
    print(
        "=== ИИ-агент поиска объявлений ==="
    )

    print(
        f"Язык: {LANGUAGE}"
    )

    print(
        f"Языки поиска: "
        f"{', '.join(SEARCH_LANGUAGES)}"
    )

    print(
        f"Исключённые языки: "
        f"{', '.join(EXCLUDE_LANGUAGES) "
        f"if EXCLUDE_LANGUAGES else 'нет'}"
    )

    print(
        f"Тип задач: {TASK_TYPE}"
    )

    print(
        "Конфигурация загружена из "
        "agent_config.json"
    )
