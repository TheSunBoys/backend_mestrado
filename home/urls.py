from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('documento/', views.verificador_de_documento, name='documento'),
]