# models.py
from django.db import models

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
    cpf = models.CharField(max_length=11)  # Para criar o diretório com base no CPF
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    def get_upload_path(self):
        # Definindo o caminho para armazenar os arquivos do aluno, incluindo seu nome e CPF
        return f"alunos/{self.nome}_{self.cpf}/"
    class Meta:
        db_table = 'meu_nome_personalizado_da_tabela'
class Arquivo(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='arquivos')
    tipo = models.CharField(max_length=255)  # Para identificar o tipo de documento (Ex.: 'curriculo', 'projeto', etc.)
    arquivo = models.FileField(upload_to='')  # Usaremos a função get_upload_path para o upload

    def save(self, *args, **kwargs):
        self.arquivo.name = f"{self.aluno.get_upload_path()}{self.arquivo.name}"
        super().save(*args, **kwargs)
