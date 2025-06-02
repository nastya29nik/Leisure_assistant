from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    password_hash = models.CharField(max_length=255, verbose_name="Хэш пароля")

    def __str__(self):
        return self.username
