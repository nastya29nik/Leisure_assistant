from django.shortcuts import render
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy
from .forms import RegistrationForm, LoginForm
from django.contrib.auth import login


class RegistrationView(CreateView):
    form_class = RegistrationForm
    template_name = "users/sign.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class LoginView(FormView):
    form_class = LoginForm
    template_name = "users/login.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super().form_valid(form)
