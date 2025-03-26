from django.db import models
from django.conf import settings

class Aluno(models.Model):
    nome = models.CharField(max_length=255)
    idade = models.IntegerField()
    curso = models.CharField(max_length=255)
    ira = models.DecimalField(max_digits=4, decimal_places=2)
    email = models.EmailField()
    lattes = models.URLField()
    github = models.URLField()
    interesse = models.CharField(max_length=255)
    genero = models.CharField(max_length=50)
    ppi = models.CharField(max_length=50)
    cpf = models.CharField(max_length=11) 
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    def get_upload_path(self):
        return f"alunos/{self.nome}_{self.cpf}/"
    class Meta:
        db_table = 'alunos'

def arquivo_upload_path(instance, filename):
    aluno = instance.aluno
    return f"{aluno.get_upload_path()}{filename}"

class Arquivo(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='arquivos')
    tipo = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to=arquivo_upload_path)  

    def __str__(self):
        return f"Arquivo {self.tipo} de {self.aluno.nome}"

class Edital(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    arquivo = models.FileField(upload_to='editais/')  # Arquivos serão salvos em MEDIA_ROOT/editais/
    data_publicacao = models.DateTimeField(auto_now_add=True)
    autor = models.CharField(max_length=100) 
    ativo = models.BooleanField(default=True)
    def __str__(self):
        return self.titulo
    
class Selecao(models.Model):
    edital = models.OneToOneField(Edital, on_delete=models.CASCADE, related_name='selecao')
    professor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='selecoes_como_professor'
    )
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    
    def __str__(self):
        return f"Seleção para {self.edital.titulo}"

class Inscricao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('reprovada', 'Reprovada'),
    ]
    
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscricoes_como_aluno'
    )
    selecao = models.ForeignKey(Selecao, on_delete=models.CASCADE)
    data_inscricao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    documento = models.FileField(upload_to='inscricoes/')
    
    class Meta:
        unique_together = ('aluno', 'selecao')
    
    def __str__(self):
        return f"Inscrição de {self.aluno.username} para {self.selecao}"