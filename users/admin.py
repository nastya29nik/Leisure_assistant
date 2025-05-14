from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("username", "password_hash")}),
        ("Персональная информация", {"fields": ("first_name", "last_name")}),
    )


admin.site.register(User, CustomUserAdmin)
