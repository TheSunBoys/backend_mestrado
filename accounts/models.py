from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
class User(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Professor'),
        ('student', 'Aluno'),
    )
    cpf = models.CharField(max_length=11, unique=True, default= "00000000000")
    date_of_birth = models.DateField(default= date.today)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')