from django.contrib import admin
from .models import PlacesCategory, Place, PlacesVisited, Review


@admin.register(PlacesCategory)
class PlacesCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "short_description")
    list_filter = ("category",)
    search_fields = ("name", "description")


@admin.register(PlacesVisited)
class PlacesVisitedAdmin(admin.ModelAdmin):
    list_display = ("user", "place", "mark", "visited_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("place", "mark", "comment")
