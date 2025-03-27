from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Usuario(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
        ('admin', 'Administrador'),
    ]
    
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES)
    cpf = models.CharField(max_length=11, unique=True)
    telefone = models.CharField(max_length=15, blank=True)
    
    class Meta:
        db_table = 'usuarios'
    
    def __str__(self):
        return self.get_full_name() or self.username

class Aluno(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_aluno',
        limit_choices_to={'tipo_usuario': 'aluno'}
    )
    curso = models.CharField(max_length=255)
    ira = models.DecimalField(max_digits=4, decimal_places=2)
    github = models.URLField(blank=True)
    interesse_pesquisa = models.CharField(max_length=255, blank=True)
    genero = models.CharField(max_length=50, blank=True)
    ppi = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'alunos'
    
    def __str__(self):
        return self.usuario.get_full_name()
    
def arquivo_upload_path(instance, filename):
    aluno = instance.aluno
    return f"{aluno.get_upload_path()}{filename}"

class Professor(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_professor',
        limit_choices_to={'tipo_usuario': 'professor'}
    )
    departamento = models.CharField(max_length=100)
    lattes = models.URLField(blank=True)
    area_atuacao = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'professores'
        verbose_name_plural = "Professores"
    
    def __str__(self):
        return f"Prof. {self.usuario.get_full_name()}"

class Edital(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    arquivo = models.FileField(upload_to='editais/')
    data_publicacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='editais_criados'
    )
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.titulo

class Selecao(models.Model):
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='selecoes')
    professor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='selecoes_responsavel',
        limit_choices_to={'tipo_usuario': 'professor'}
    )
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    vagas = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"Seleção {self.edital.titulo}"

class Inscricao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('reprovada', 'Reprovada'),
    ]
    
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscricoes',
        limit_choices_to={'tipo_usuario': 'aluno'}
    )
    selecao = models.ForeignKey(Selecao, on_delete=models.CASCADE, related_name='inscricoes')
    data_inscricao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    documento = models.FileField(upload_to='inscricoes/%Y/%m/')
    observacao = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('aluno', 'selecao')
        ordering = ['-data_inscricao']
    
    def __str__(self):
        return f"Inscrição #{self.id}"