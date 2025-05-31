import requests
from django.conf import settings


def generate_summary(text, summary_type):
    """Генерирует сводку текста через YandexGPT"""
    if not text:
        return f"Нет {summary_type} комментариев"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.YANDEX_IAM_TOKEN}",
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
                "text": f"Суммаризируй основные темы из отзывов: {text[:15000]}",  # Ограничение длины
            },
        ],
    }

    try:
        response = requests.post(
            settings.YANDEX_GPT_API_URL, headers=headers, json=prompt, timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return result["result"]["alternatives"][0]["message"]["text"]
    except Exception as e:
        return f"Ошибка суммаризации: {str(e)}"
