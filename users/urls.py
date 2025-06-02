from django.urls import path
from .views import RegistrationView, LoginView, AccountView

app_name = "users"

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("account/", AccountView.as_view(), name="account"),
]
