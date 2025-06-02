import requests
from django.conf import settings


def generate_summary(texts, summary_type):
    if not texts:
        return f"Нет {summary_type} комментариев"

    combined_text = "\n".join(texts)[:15000]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.YANDEX_API_KEY}",
        "x-folder-id": settings.YANDEX_FOLDER_ID,
    }

    prompt = {
        "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": 500},
        "messages": [
            {
                "role": "system",
                "text": "Ты опытный аналитик отзывов. Сгенерируй краткую сводку основных мыслей.",
            },
            {
                "role": "user",
                "text": f"Суммаризируй основные темы из отзывов: {combined_text}",
            },
        ],
    }

    try:
        response = requests.post(
            settings.YANDEX_GPT_API_URL,
            headers=headers,
            json={"model": prompt},
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
        return result["result"]["alternatives"][0]["message"]["text"]
    except Exception as e:
        return f"Ошибка суммаризации: {str(e)}"
