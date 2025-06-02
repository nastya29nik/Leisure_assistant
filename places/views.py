from django.http import JsonResponse
from django.db.models import Avg
from django.shortcuts import render
from django.contrib import messages
from django.views.generic import ListView, CreateView, FormView, TemplateView
from .models import Place, PlacesCategory, PlacesVisited, Review
from .forms import PlaceForm, FeedbackForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
import requests
from yandexgptlite import YandexGPTLite
from django.conf import settings
from django.core.cache import cache


class PlaceListView(ListView):
    model = Place
    template_name = "places/place_list.html"
    context_object_name = "places"


class AddPlaceView(CreateView):
    form_class = PlaceForm
    template_name = "places/add_place.html"
    success_url = reverse_lazy("users:account")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = PlacesCategory.objects.all()
        return context

    def form_valid(self, form):
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Ошибка: {error}")
        return super().form_invalid(form)


class AddFeedbackView(LoginRequiredMixin, FormView):
    template_name = "places/feedback.html"
    form_class = FeedbackForm
    success_url = reverse_lazy("users:account")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        place = form.cleaned_data["place"]
        mark = form.cleaned_data["mark"]
        feedback = form.cleaned_data["feedback"]

        obj, created = PlacesVisited.objects.update_or_create(
            user=self.request.user,
            place=place,
            defaults={"mark": mark, "feedback": feedback},
        )

        return super().form_valid(form)


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
            place.image.url
            if place.image
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
                "image": image_url,
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
        place.image.url
        if place.image
        else f"{settings.STATIC_URL}images/default-place.jpg"
    )
    reviews_count = Review.objects.filter(place=place).count()
    data = {
        "id": place.id,
        "name": place.name,
        "image": image_url,
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
    """Генерирует сводку отзывов о месте через YandexGPT API"""
    try:
        logger.info(f"Запрос сводки для места ID: {place_id}")
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        logger.error(f"Место {place_id} не найдено")
        return JsonResponse({"error": "Место не найдено"}, status=404)

    # Проверка кэша
    cache_key = f"place_summary_{place_id}"
    if cached := cache.get(cache_key):
        logger.info(f"Возвращаем кэшированную сводку для места {place_id}")
        return JsonResponse(cached)

    # Сбор всех отзывов
    reviews = (
        Review.objects.filter(place=place)
        .exclude(comment__isnull=True)
        .exclude(comment__exact="")
        .values_list("comment", flat=True)
    )

    # Сбор фидбэка из посещений
    visits = (
        PlacesVisited.objects.filter(place=place)
        .exclude(feedback__isnull=True)
        .exclude(feedback__exact="")
        .values_list("feedback", flat=True)
    )

    all_comments = list(reviews) + list(visits)

    if not all_comments:
        logger.info(f"Нет комментариев для места {place_id}")
        result = {"summary": "Отзывов пока нет!"}
        cache.set(cache_key, result, 3600)  # Кэшируем на 1 час
        return JsonResponse(result)

    logger.info(f"Найдено {len(all_comments)} комментариев для места {place_id}")

    # Формируем текст для суммаризации (ограничиваем длину)
    comments_text = "\n".join(all_comments)[:15000]

    try:
        # Формируем запрос к YandexGPT
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
            "x-folder-id": settings.YANDEX_FOLDER_ID,
        }

        prompt = {
            "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt-lite/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 1000,  # Увеличили лимит для более полных ответов
            },
            "messages": [
                {
                    "role": "system",
                    "text": (
                        "Ты опытный аналитик отзывов. Сгенерируй краткую сводку основных мыслей. "
                        "Выдели ключевые положительные и отрицательные аспекты. "
                        "Будь объективным и лаконичным. "
                        "Используй формат: "
                        "1. Основные преимущества: [перечисли 3-5 пунктов] "
                        "2. Что можно улучшить: [перечисли 3-5 пунктов] "
                        "3. Общее впечатление: [краткое резюме]"
                    ),
                },
                {
                    "role": "user",
                    "text": f"Проанализируй отзывы посетителей: {comments_text}",
                },
            ],
        }

        logger.debug(
            f"Отправка запроса к YandexGPT: {json.dumps(prompt, ensure_ascii=False)[:500]}..."
        )

        # Отправляем запрос с увеличенным таймаутом
        response = requests.post(
            settings.YANDEX_GPT_API_URL,
            headers=headers,
            json=prompt,
            timeout=30,  # Увеличенный таймаут
        )

        logger.debug(f"Ответ от YandexGPT: статус {response.status_code}")

        # Проверяем статус ответа
        if response.status_code != 200:
            logger.error(
                f"Ошибка YandexGPT: {response.status_code} - {response.text[:500]}"
            )
            return JsonResponse(
                {
                    "error": f"Ошибка API YandexGPT: {response.status_code}",
                    "details": response.text[:1000],
                },
                status=500,
            )

        # Парсим ответ
        result_data = response.json()
        logger.debug(
            f"Полный ответ YandexGPT: {json.dumps(result_data, ensure_ascii=False)[:500]}..."
        )

        # Извлекаем текст сводки
        if (
            "result" in result_data
            and "alternatives" in result_data["result"]
            and result_data["result"]["alternatives"]
        ):
            summary = result_data["result"]["alternatives"][0]["message"]["text"]
        else:
            logger.error(
                f"Неожиданный формат ответа: {json.dumps(result_data, indent=2)}"
            )
            summary = "Не удалось обработать ответ от YandexGPT"

        # Формируем результат
        result = {"summary": summary}

        # Кэшируем результат на 1 час
        cache.set(cache_key, result, 3600)
        logger.info(f"Сводка успешно сгенерирована для места {place_id}")

        return JsonResponse(result)

    except requests.Timeout:
        logger.error("Таймаут при запросе к YandexGPT")
        return JsonResponse(
            {"error": "Превышено время ожидания ответа от YandexGPT"}, status=504
        )

    except requests.ConnectionError:
        logger.error("Ошибка подключения к YandexGPT")
        return JsonResponse(
            {"error": "Ошибка подключения к YandexGPT. Проверьте интернет-соединение."},
            status=503,
        )

    except Exception as e:
        logger.exception(f"Неизвестная ошибка при генерации сводки: {str(e)}")
        return JsonResponse(
            {"error": f"Внутренняя ошибка сервера: {str(e)}"}, status=500
        )
