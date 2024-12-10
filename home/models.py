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
    cpf = models.CharField(max_length=11) 
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    def get_upload_path(self):
        return f"alunos/{self.nome}_{self.cpf}/"
    class Meta:
        db_table = 'meu_nome_personalizado_da_tabela'

def arquivo_upload_path(instance, filename):
    aluno = instance.aluno
    return f"{aluno.get_upload_path()}{filename}"

class Arquivo(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='arquivos')
    tipo = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to=arquivo_upload_path)  

    def __str__(self):
        return f"Arquivo {self.tipo} de {self.aluno.nome}"
