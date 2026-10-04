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

CONFIG_INCLUDED_KEYWORDS = [
    word.lower()
    for word in CONFIG.get("include", [])
]


# Дополнительные темы работ.
# Они встроены в код, поэтому классификатор
# не зависит только от agent_config.json.
BUILTIN_REPAIR_TOPICS = [
    # Сантехника
    "сантехник",
    "сантехника",
    "смеситель",
    "кран",
    "сифон",
    "унитаз",
    "труба",
    "трубы",
    "водопровод",
    "протечка",
    "течет",
    "течёт",
    "засор",
    "бойлер",
    "водонагреватель",

    # Электрика
    "электрик",
    "электрика",
    "розетка",
    "розетки",
    "выключатель",
    "выключатели",
    "проводка",
    "лампа",
    "лампы",
    "светильник",
    "освещение",
    "электричество",

    # Кондиционирование
    "кондиционер",
    "кондиционеры",
    "кондиционирование",
    "вентиляция",

    # Ремонт и отделка
    "ремонт",
    "ремонт квартиры",
    "ремонт дома",
    "отделка",
    "отделочные работы",
    "штукатурка",
    "штукатур",
    "шпатлевка",
    "шпаклевка",
    "маляр",
    "покраска",
    "обои",
    "гипсокартон",
    "плитка",
    "плиточник",
    "кафель",
    "затирка",
    "ламинат",
    "паркет",
    "напольное покрытие",
    "пол",
    "плинтус",
    "потолок",

    # Двери и окна
    "дверь",
    "двери",
    "замок",
    "замки",
    "окно",
    "окна",
    "стекло",
    "стеклопакет",
    "жалюзи",
    "москитная сетка",

    # Мебель
    "мебель",
    "шкаф",
    "шкафа",
    "шкафы",
    "комод",
    "комоды",
    "кровать",
    "кровати",
    "стол",
    "столы",
    "стул",
    "стулья",
    "тумба",
    "тумбы",
    "диван",
    "диваны",
    "кухня",
    "кухни",
    "гардероб",
    "гардеробная",
    "полка",
    "полки",
    "карниз",
    "карнизы",
    "сборка мебели",
    "собрать мебель",
    "установка мебели",
    "установить мебель",

    # Бытовая техника
    "бытовая техника",
    "стиральная машина",
    "стиральная",
    "посудомоечная машина",
    "посудомойка",
    "холодильник",
    "холодильники",
    "духовка",
    "духовой шкаф",
    "варочная панель",
    "плита",
    "вытяжка",
    "микроволновка",
    "микроволновая печь",

    # Монтаж и установка
    "монтаж",
    "монтажные работы",
    "установка",
    "установить",
    "установки",
    "подключить",
    "подключение",
    "повесить",
    "закрепить",
    "крепление",
    "собрать",
    "сборка",
    "заменить",
    "замена",
    "починить",
    "починка",
    "отремонтировать",

    # Прочее
    "мелкий ремонт",
    "мастер",
    "строитель",
]


INCLUDED_KEYWORDS = list(
    dict.fromkeys(
        CONFIG_INCLUDED_KEYWORDS
        + BUILTIN_REPAIR_TOPICS
    )
)


VACANCY_MARKERS = [
    "вакансия",
    "вакансии",
    "ищем сотрудника",
    "ищем работников",
    "ищем работника",
    "требуется сотрудник",
    "требуется сотрудник",
    "требуется работник",
    "требуются работники",
    "требуется персонал",
    "нужен сотрудник",
    "нужен работник",
    "нужны работники",
    "работа официальная",
    "официальное трудоустройство",
    "официальная работа",
    "трудоустройство",
    "график работы",
    "сменный график",
    "полный рабочий день",
    "неполный рабочий день",
    "смена",
    "ставка",
    "заработная плата",
    "зарплата",
    "оклад",
    "резюме",
    "ищу работу",
    "работа в компании",
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
    "услуги мастера",
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
    # Прямой поиск мастера
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

    # Рекомендации
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

    # Требуется
    "требуется мастер",
    "требуется сантехник",
    "требуется электрик",
    "требуется плиточник",
    "требуется специалист",

    # Нужно сделать
    "нужно установить",
    "нужно заменить",
    "нужно отремонтировать",
    "нужно починить",
    "нужно собрать",
    "нужно подключить",
    "нужно повесить",
    "нужно закрепить",
    "нужно покрасить",
    "нужно уложить",
    "нужно смонтировать",

    "надо установить",
    "надо заменить",
    "надо отремонтировать",
    "надо починить",
    "надо собрать",
    "надо подключить",
    "надо повесить",
    "надо закрепить",
    "надо покрасить",
    "надо уложить",
    "надо смонтировать",

    "необходимо установить",
    "необходимо заменить",
    "необходимо отремонтировать",
    "необходимо починить",
    "необходимо собрать",
    "необходимо подключить",
    "необходимо повесить",
    "необходимо закрепить",
    "необходимо покрасить",
    "необходимо уложить",
    "необходимо смонтировать",

    # Желание клиента
    "хочу установить",
    "хочу заменить",
    "хочу отремонтировать",
    "хочу починить",
    "хочу собрать",
    "хочу подключить",
    "хочу повесить",
    "хочу закрепить",

    # Кто занимается
    "кто занимается",
    "кто делает",
    "кто устанавливает",
    "кто ремонтирует",
    "кто собирает",
    "кто подключает",
    "кто может установить",
    "кто может заменить",
    "кто может починить",
    "кто может собрать",

    # Есть ли специалист
    "есть мастер",
    "есть сантехник",
    "есть электрик",
    "есть плиточник",
    "есть специалист",
]


PROBLEM_MARKERS = [
    "сломался",
    "сломалась",
    "сломалось",
    "сломались",
    "не работает",
    "не работают",
    "не включается",
    "не включаются",
    "не выключается",
    "не выключаются",
    "не греет",
    "не греют",
    "не охлаждает",
    "не охлаждают",
    "течёт",
    "течет",
    "протекает",
    "протекают",
    "капает",
    "капают",
    "засорился",
    "засорилась",
    "засорились",
    "засор",
    "протечка",
    "протечки",
    "трещина",
    "трещины",
    "треснул",
    "треснула",
    "разбилось",
    "разбилась",
    "разбит",
    "разбито",
    "сломано",
    "неисправен",
    "неисправна",
    "неисправность",
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


def contains_any(text, markers):
    text_lower = text.lower()

    return any(
        marker in text_lower
        for marker in markers
    )


def is_vacancy(text):
    if not text:
        return False

    return contains_any(
        text,
        VACANCY_MARKERS
    )


def has_client_request(text):
    if not text:
        return False

    return contains_any(
        text,
        CLIENT_REQUEST_MARKERS
    )


def has_problem(text):
    if not text:
        return False

    return contains_any(
        text,
        PROBLEM_MARKERS
    )


def has_repair_topic(text):
    if not text:
        return False

    return contains_any(
        text,
        INCLUDED_KEYWORDS
    )


def is_service_offer(text):
    if not text:
        return False

    text_lower = text.lower()

    if contains_any(
        text,
        SERVICE_OFFER_MARKERS
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
        "недорогие",
        "цена",
        "цены",
        "от 20€",
        "от 20 €",
        "от 30€",
        "от 30 €",
        "доступно",
        "по доступной цене",
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

    # Только русский язык
    if (
        LANGUAGE == "ru"
        and not is_russian_text(text)
    ):
        return False

    # Исключённые темы
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in text_lower:
            return False

    # Вакансии
    if is_vacancy(text):
        return False

    # Реклама услуг
    if is_service_offer(text):
        return False

    # Должна присутствовать ремонтная /
    # бытовая тема
    if not has_repair_topic(text):
        return False

    # Должен быть признак реальной заявки
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
        reason = "Предложение услуг мастера."

    elif is_vacancy(text):
        reason = "Вакансия работодателя."

    elif (
        LANGUAGE == "ru"
        and not is_russian_text(text)
    ):
        reason = "Объявление не является русскоязычным."

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


def search_web(
    query,
    recency_minutes=7200
):
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


def run_agent(
    url,
    goal,
    timeout=120
):
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
            value.replace(
                "Z",
                "+00:00"
            )
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


def is_fresh_date(
    value,
    days=5
):
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

    if "facebook.com" not in url_lower:
        return False

    forbidden = [
        "/marketplace/",
        "/events/",
        "/watch/",
        "/reels/",
        "/videos/"
    ]

    if any(
        part in url_lower
        for part in forbidden
    ):
        return False

    return True


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
        f"Количество ключевых слов: "
        f"{len(INCLUDED_KEYWORDS)}"
    )

    print(
        "Конфигурация загружена из "
        "agent_config.json"
    )
