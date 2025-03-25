from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import dashboard

urlpatterns = [
    path('',views.home, name='home'),
    path('cadastro/',views.cadastro_aluno, name='cadastro'),
    path('avaliar/', views.verificador_de_documento, name='avaliar'),
    path('area-professor/', views.area_professor, name='area_professor'),
    path('deletar-aluno/<int:aluno_id>/', views.deletar_aluno, name='deletar_aluno'),
    path('dashboard/', dashboard, name='dashboard'),
    path('editais', views.index, name='index_editais'),
    path('novo/', views.criar_edital, name='criar_edital'),
    path('<int:id>/editar/', views.editar_edital, name='editar_edital'),
    path('<int:id>/deletar/', views.deletar_edital, name='deletar_edital'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)