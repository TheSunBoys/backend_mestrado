from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticação
    path('registro/', views.registrar_usuario, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard e áreas
    path('', views.dashboard, name='home'),
    path('aluno/', views.area_aluno, name='area_aluno'),
    path('professor/', views.area_professor, name='area_professor'),
    path('analisar-documentos/', views.analisar_documentos, name='analisar_documentos'),
    
    path('blog/', views.blog, name='blog'),
    # Perfis
    path('completar-perfil/aluno/', views.completar_perfil_aluno, name='completar_perfil_aluno'),
    path('completar-perfil/professor/', views.completar_perfil_professor, name='completar_perfil_professor'),
    
    # Editais
    path('editais/', views.listar_editais, name='listar_editais'),
    path('editais/novo/', views.criar_edital, name='criar_edital'),
    path('editais/<int:pk>/', views.exibir_edital, name='exibir_edital'),
    path('editais/<int:pk>/editar/', views.editar_edital, name='editar_edital'),
    path('editais/<int:pk>/excluir/', views.excluir_edital, name='excluir_edital'),
    
    # Seleções
    path('selecoes/<int:edital_id>/nova/', views.criar_selecao, name='criar_selecao'),
    path('selecoes/<int:pk>/', views.detalhes_selecao, name='detalhes_selecao'),
    path('selecoes/<int:pk>/inscrever/', views.inscrever_selecao, name='inscrever_selecao'),
    path('selecoes/<int:pk>/editar/', views.editar_selecao, name='editar_selecao'),


    
    path('avaliar-inscricao/<int:inscricao_id>/', views.avaliar_inscricao, name='avaliar_inscricao'),
    # Admin
    path('admin/usuarios/', views.administrar_usuarios, name='administrar_usuarios'),
]