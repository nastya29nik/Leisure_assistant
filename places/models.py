from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=64, verbose_name="Название категории")
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return self.name


class Place(models.Model):
    name = models.CharField(max_length=254, verbose_name="Название")
    image_path = models.CharField(max_length=255, verbose_name="Путь к изображению")
    description = models.TextField(verbose_name="Описание")
    short_description = models.CharField(max_length=64, verbose_name="Краткое описание")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name="Категория"
    )

    def __str__(self):
        return self.name


class UserPlace(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    place = models.ForeignKey(Place, on_delete=models.CASCADE, verbose_name="Место")
    mark = models.IntegerField(
        choices=[(i, i) for i in range(1, 11)], verbose_name="Оценка"
    )
    feedback = models.TextField(verbose_name="Комментарий", blank=True)
    visited_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата посещения")

    def __str__(self):
        return f"{self.user} → {self.place}"
