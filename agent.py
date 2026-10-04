import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


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
    "резюме",
    "ищу работу",
]


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
    "обращайтесь",
    "звоните",
    "пишите в личку",
    "пишите в лс",
    "пишите мне",
    "whatsapp:",
    "viber:",
    "telegram:",
]


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
]


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


def is_russian_text(text):
    if not text:
        return False

    russian_letters = (
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    )

    count = sum(
        1
        for char in text.lower()
        if char in russian_letters
    )

    return count >= 5


def is_vacancy(text):
    if not text:
        return False

    text_lower = text.lower()

    return any(
        marker in text_lower
        for marker in VACANCY_MARKERS
    )


def has_client_request(text):
    if not text:
        return False

    text_lower = text.lower()

    return any(
        marker in text_lower
        for marker in CLIENT_REQUEST_MARKERS
    )


def has_problem(text):
    if not text:
        return False

    text_lower = text.lower()

    return any(
        marker in text_lower
        for marker in PROBLEM_MARKERS
    )


def has_repair_topic(text):
    if not text:
        return False

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in INCLUDED_KEYWORDS
    )


def is_service_offer(text):
    if not text:
        return False

    text_lower = text.lower()

    if any(
        marker in text_lower
        for marker in SERVICE_OFFER_MARKERS
    ):
        return True

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

    return (
        any(
            word in text_lower
            for word in service_words
        )
        and
        any(
            word in text_lower
            for word in advertising_words
        )
    )


def is_repair_request(text):
    if not text:
        return False

    text_lower = text.lower()

    if (
        LANGUAGE == "ru"
        and not is_russian_text(text)
    ):
        return False

    for keyword in EXCLUDED_KEYWORDS:
        if keyword in text_lower:
            return False

    if is_vacancy(text):
        return False

    if is_service_offer(text):
        return False

    if not has_repair_topic(text):
        return False

    if has_client_request(text):
        return True

    if has_problem(text):
        return True

    return False


def analyze_ad(text):
    if is_repair_request(text):
        return {
            "match": True,
            "text": text,
            "reason": (
                "Реальная заявка клиента "
                "на ремонтные или бытовые работы."
            )
        }

    if is_service_offer(text):
        reason = (
            "Предложение услуг мастера."
        )
    elif is_vacancy(text):
        reason = (
            "Вакансия работодателя."
        )
    elif (
        LANGUAGE == "ru"
        and not is_russian_text(text)
    ):
        reason = (
            "Объявление не является русскоязычным."
        )
    elif has_repair_topic(text):
        reason = (
            "Есть ремонтная тематика, но нет "
            "признаков заявки клиента."
        )
    else:
        reason = (
            "Объявление не соответствует критериям."
        )

    return {
        "match": False,
        "text": text,
        "reason": reason
    }


def search_web(query, recency_minutes=7200):
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
            "language": "ru",
            "recency_minutes": recency_minutes
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def run_agent(url, goal, timeout=120):
    api_key = os.environ.get(
        "TINYFISH_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "Не найден секрет TINYFISH_API_KEY"
        )

    response = requests.post(
        "https://agent.tinyfish.ai/v1/automation/run",
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        },
        json={
            "url": url,
            "goal": goal,
            "browser_profile": "lite"
        },
        timeout=timeout
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "COMPLETED":
        raise RuntimeError(
            "TinyFish Agent завершился со статусом: "
            f"{data.get('status')}"
        )

    result = data.get("result")

    if result is None:
        result = data.get("resultJson")

    if isinstance(result, dict):
        return result

    if isinstance(result, str):
        try:
            parsed = json.loads(result)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

        return {
            "raw_result": result
        }

    return {
        "raw_result": result
    }


def parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    try:
        result = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if result.tzinfo is None:
            result = result.replace(
                tzinfo=timezone.utc
            )

        return result.astimezone(
            timezone.utc
        )

    except ValueError:
        pass

    patterns = [
        r"(\d{4})-(\d{2})-(\d{2})",
        r"(\d{2})\.(\d{2})\.(\d{4})",
        r"(\d{2})/(\d{2})/(\d{4})"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            value
        )

        if not match:
            continue

        groups = match.groups()

        try:
            if len(groups[0]) == 4:
                year, month, day = map(
                    int,
                    groups
                )
            else:
                day, month, year = map(
                    int,
                    groups
                )

            return datetime(
                year,
                month,
                day,
                tzinfo=timezone.utc
            )

        except ValueError:
            continue

    return None


def is_fresh_date(value, days=5):
    parsed = parse_date(value)

    if not parsed:
        return False

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=days)
    )

    return parsed >= cutoff


def is_facebook_candidate(url):
    if not url:
        return False

    url_lower = url.lower()

    if "facebook.com/groups/" not in url_lower:
        return False

    forbidden = [
        "/videos/",
        "/reels/",
        "/watch/",
        "/events/",
        "/marketplace/"
    ]

    return not any(
        part in url_lower
        for part in forbidden
    )


if __name__ == "__main__":
    print(
        "=== ИИ-АГЕНТ ПОИСКА ОБЪЯВЛЕНИЙ ==="
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
        f"{', '.join(EXCLUDE_LANGUAGES) if EXCLUDE_LANGUAGES else 'нет'}"
    )

    print(
        f"Тип задач: {TASK_TYPE}"
    )

    print(
        "Конфигурация загружена из "
        "agent_config.json"
    )
