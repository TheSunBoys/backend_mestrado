from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
class Usuario(AbstractUser):
    class Meta:
        db_table = 'auth_user' 
    TIPO_USUARIO_CHOICES = (
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
    )
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES)