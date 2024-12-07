from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('cadastro/',views.cadastro_aluno, name='cadastro'),
    path('documento/', views.verificador_de_documento, name='documento'),
    path('area-professor/', views.area_professor, name='area_professor'),
    path('deletar-aluno/<int:aluno_id>/', views.deletar_aluno, name='deletar_aluno'),
]