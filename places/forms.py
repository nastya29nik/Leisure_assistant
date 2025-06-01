from django import forms
from .models import Place, PlacesVisited
from django.core.exceptions import ValidationError


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ["name", "image", "description", "short_description", "category"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "short_description": forms.TextInput(attrs={"maxlength": 64}),
        }
        labels = {
            "name": "Название места",
            "description": "Описание",
            "short_description": "Краткое описание",
            "category": "Категория",
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Place.objects.filter(name__iexact=name).exists():
            raise ValidationError("Место с таким названием уже существует!")
        return name


class FeedbackForm(forms.ModelForm):
    place = forms.ModelChoiceField(
        queryset=Place.objects.none(),
        widget=forms.Select(attrs={"class": "form-input"}),
    )

    class Meta:
        model = PlacesVisited
        fields = ["place", "mark", "feedback"]
        widgets = {
            "feedback": forms.Textarea(attrs={"rows": 4}),
            "mark": forms.RadioSelect(choices=[(i, i) for i in range(1, 11)]),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        visited_places = (
            PlacesVisited.objects.filter(user=user).select_related("place").distinct()
        )
        place_ids = [vp.place.id for vp in visited_places]
        self.fields["place"].queryset = Place.objects.filter(id__in=place_ids)
