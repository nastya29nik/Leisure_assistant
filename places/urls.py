from django.urls import path
from . import views

app_name = "places"

urlpatterns = [
    path("add/", views.AddPlaceView.as_view(), name="add_place"),
    path("feedback/", views.AddFeedbackView.as_view(), name="add_feedback"),
    path("places/", views.places_api, name="places_api"),
    path("place/<int:place_id>/", views.place_detail_api, name="place_detail_api"),
    path("mark_visited/", views.mark_visited, name="mark_visited"),
    path("place/<int:place_id>/summary/", views.place_summary, name="place_summary"),
]
