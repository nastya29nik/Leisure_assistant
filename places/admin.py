from django.contrib import admin
from .models import Category, Place, UserPlace


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "short_description")
    list_filter = ("category",)


@admin.register(UserPlace)
class UserPlaceAdmin(admin.ModelAdmin):
    list_display = ("user", "place", "mark", "visited_at")
    search_fields = ("user__username", "place__name")
