from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('inscricao/',views.envio_de_arquivo, name='envio_arquivo'),
    path('documento/', views.verificador_de_documento, name='documento'),
]