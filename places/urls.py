from django.urls import path
from . import views

app_name = "places"

urlpatterns = [
    path("", views.PlaceListView.as_view(), name="place_list"),
    path("add/", views.AddPlaceView.as_view(), name="add_place"),
    path("feedback/", views.AddFeedbackView.as_view(), name="add_feedback"),
]
