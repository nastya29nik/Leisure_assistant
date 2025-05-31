from django.shortcuts import render
from django.contrib import messages
from django.views.generic import ListView, CreateView, FormView
from .models import Place, PlacesCategory, PlacesVisited
from .forms import PlaceForm, FeedbackForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


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
