from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label="Имя", widget=forms.TextInput(attrs={"class": "form-input"})
    )
    last_name = forms.CharField(
        label="Фамилия", widget=forms.TextInput(attrs={"class": "form-input"})
    )
    username = forms.CharField(
        label="Логин", widget=forms.TextInput(attrs={"class": "form-input"})
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "password1", "password2"]


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин", widget=forms.TextInput(attrs={"class": "form-input"})
    )
    password = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-input"})
    )
