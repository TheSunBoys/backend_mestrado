from django import forms
from .models import Aluno, Arquivo
from .models import Edital

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = [
            'nome', 'idade', 'curso', 'ira', 'email', 
            'lattes', 'github', 'interesse', 'genero', 
            'ppi', 'cpf'
        ]
        widgets = {
            'interesse': forms.Select(choices=[('ia', 'Otimização de IA'), ('engenharia-software', 'Engenharia de Software')]),
            'genero': forms.Select(choices=[('homem', 'Homem'), ('mulher', 'Mulher'), ('outro', 'Outro')]),
            'ppi': forms.Select(choices=[('preto', 'Preto'), ('pardo', 'Pardo'), ('indigena', 'Indígena'), ('nao', 'Não')]),
        }

class ArquivoForm(forms.ModelForm):
    class Meta:
        model = Arquivo
        fields = ['tipo', 'arquivo']

class EditalForm(forms.ModelForm):
    class Meta:
        model = Edital
        fields = ['titulo', 'descricao', 'arquivo', 'autor', 'ativo']