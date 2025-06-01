from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class PlacesCategory(models.Model):
    name = models.CharField(max_length=64)

    class Meta:
        db_table = "places_category"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Place(models.Model):
    name = models.CharField(max_length=254)
    image = models.ImageField(
        upload_to="places/images/",
        blank=True,
        null=True,
        default="images/default-place.jpg",
    )
    description = models.TextField(blank=True, null=True)
    short_description = models.CharField(max_length=64, blank=True, null=True)
    category = models.ForeignKey(
        PlacesCategory, on_delete=models.CASCADE, db_column="category_id"
    )

    class Meta:
        db_table = "places"

    def __str__(self):
        return self.name


class PlacesVisited(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mark = models.IntegerField(
        choices=[(i, i) for i in range(1, 11)],
        null=True,
        blank=True,
        verbose_name="Оценка",
    )
    feedback = models.TextField(null=True, blank=True, verbose_name="Комментарий")
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "places_visited"

    def __str__(self):
        return f"{self.user.username} visited {self.place.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.mark or self.feedback:
            Review.objects.create(
                place=self.place, mark=self.mark, comment=self.feedback
            )


class Review(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    mark = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "reviews"

    def __str__(self):
        return f"Review for {self.place.name}"
