from django.http import JsonResponse
from django.db.models import Avg
from .models import Place, PlacesCategory, PlacesVisited, Review
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt  # Добавлен импорт
from django.contrib.auth.decorators import login_required  # Добавлен импорт
from django.views.decorators.http import require_POST  # Добавлен импорт
import json
import requests
from django.conf import settings
from .utils import generate_summary
from django.core.cache import cache


class HomeView(TemplateView):
    template_name = "places/home.html"


def places_api(request):
    category_slug = request.GET.get("category")
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 5))

    if not category_slug:
        return JsonResponse({"error": 'Parameter "category" is required'}, status=400)

    category_mapping = {
        "walk": "Прогулка",
        "theater": "Театр",
        "museum": "Музей",
        "restaurant": "Ресторан",
        "cafe": "Кафе",
        "park": "Парк аттракционов",
        "pool": "Бассейн",
        "kids": "Детский досуг",
        "coworking": "Коворкинг",
        "cinema": "Кино",
        "entertainment": "Развлекательные центры",
    }

    russian_category = category_mapping.get(category_slug.lower())
    if not russian_category:
        return JsonResponse({"error": "Category not found"}, status=404)

    try:
        category = PlacesCategory.objects.get(name__iexact=russian_category)
    except PlacesCategory.DoesNotExist:
        return JsonResponse({"error": "Category not found"}, status=404)

    places = (
        Place.objects.filter(category=category)
        .annotate(avg_rating=Avg("review__mark"))
        .order_by("-avg_rating")[offset : offset + limit]
    )

    places_data = []
    for place in places:
        image_url = (
            place.image_path.url
            if place.image_path
            else f"{settings.STATIC_URL}images/default-place.jpg"
        )
        is_visited = False
        if request.user.is_authenticated:
            is_visited = PlacesVisited.objects.filter(
                user=request.user, place=place
            ).exists()

        places_data.append(
            {
                "id": place.id,
                "name": place.name,
                "image_path": image_url,
                "short_description": place.short_description or "",
                "rating": round(float(place.avg_rating), 1) if place.avg_rating else 0,
                "description": place.description or "Нет описания",
                "is_visited": is_visited,
            }
        )

    return JsonResponse({"places": places_data})


def place_detail_api(request, place_id):
    try:
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        return JsonResponse({"error": "Place not found"}, status=404)

    avg_rating = Review.objects.filter(place=place).aggregate(Avg("mark"))["mark__avg"]

    is_visited = False
    if request.user.is_authenticated:
        is_visited = PlacesVisited.objects.filter(
            user=request.user, place=place
        ).exists()

    image_url = (
        place.image_path.url
        if place.image_path
        else f"{settings.STATIC_URL}images/default-place.jpg"
    )
    reviews_count = Review.objects.filter(place=place).count()
    data = {
        "id": place.id,
        "name": place.name,
        "image_path": image_url,
        "description": place.description or "Нет описания",
        "rating": round(float(avg_rating), 1) if avg_rating else 0,
        "is_visited": is_visited,
        "reviews_count": reviews_count,
    }
    return JsonResponse(data)


@csrf_exempt
@login_required
@require_POST
def mark_visited(request):
    try:
        data = json.loads(request.body)
        place_id = data.get("place_id")
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON format"}, status=400
        )
    if not place_id:
        return JsonResponse(
            {"status": "error", "message": "Missing place_id parameter"}, status=400
        )

    try:
        place = Place.objects.get(id=place_id)
        user = request.user
    except Place.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Place not found"}, status=404
        )
    visited, created = PlacesVisited.objects.get_or_create(
        user=user, place=place, defaults={"mark": None, "feedback": None}
    )

    if created:
        return JsonResponse(
            {
                "status": "added",
                "message": "Place marked as visited",
                "place_id": place.id,
                "place_name": place.name,
            }
        )
    else:
        return JsonResponse(
            {
                "status": "exists",
                "message": "Place already marked",
                "place_id": place.id,
                "place_name": place.name,
            }
        )


import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def place_summary(request, place_id):
    try:
        logger.info(f"Requested summary for place {place_id}")
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        logger.error(f"Place {place_id} not found")
        return JsonResponse({"error": "Place not found"}, status=404)
    try:
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        return JsonResponse({"error": "Place not found"}, status=404)

    cache_key = f"place_summary_{place_id}"
    if cached := cache.get(cache_key):
        return JsonResponse(cached)

    reviews = (
        Review.objects.filter(place=place)
        .exclude(comment__exact="")
        .values_list("comment", flat=True)
    )
    visits = (
        PlacesVisited.objects.filter(place=place)
        .exclude(feedback__exact="")
        .values_list("feedback", flat=True)
    )

    all_comments = list(reviews) + list(visits)

    if not all_comments:
        result = {
            "positive": "Нет отзывов для анализа",
            "negative": "Нет отзывов для анализа",
        }
        cache.set(cache_key, result, 3600)
        return JsonResponse(result)

    # Разделяем на положительные и отрицательные
    positive_comments = []
    negative_comments = []

    for comment in all_comments:
        # Простая эвристика: считаем комментарий положительным, если он содержит позитивные слова
        positive_words = [
            "отличн",
            "прекрасн",
            "рекоменд",
            "супер",
            "замечательн",
            "довол",
            "понравил",
            "восхитительн",
        ]
        negative_words = [
            "плох",
            "ужасн",
            "разочарован",
            "недоволен",
            "не понравил",
            "отвратительн",
            "не рекомендую",
        ]

        if any(word in comment.lower() for word in positive_words):
            positive_comments.append(comment)
        elif any(word in comment.lower() for word in negative_words):
            negative_comments.append(comment)

    result = {
        "positive": generate_summary(positive_comments, "положительных"),
        "negative": generate_summary(negative_comments, "отрицательных"),
    }

    cache.set(cache_key, result, 3600)  # Кешируем на 1 час
    return JsonResponse(result)


def generate_summary(texts, summary_type):
    """Генерирует сводку текста через YandexGPT"""
    if not texts:
        return f"Нет {summary_type} комментариев"

    combined_text = "\n".join(texts)[:15000]  # Ограничение длины

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.YANDEX_API_KEY}",
        "x-folder-id": settings.YANDEX_FOLDER_ID,
    }

    prompt = {
        "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt-lite/latest",
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
            settings.YANDEX_GPT_API_URL, headers=headers, json=prompt, timeout=15
        )
        response.raise_for_status()
        result = response.json()
        return result["result"]["alternatives"][0]["message"]["text"]
    except Exception as e:
        return f"Ошибка суммаризации: {str(e)}"
