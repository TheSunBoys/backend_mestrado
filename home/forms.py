from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Aluno, Professor, Inscricao, Edital, Selecao
from django.utils import timezone

class UsuarioForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'cpf', 'telefone', 'tipo_usuario']

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['curso', 'ira', 'github', 'interesse_pesquisa', 'genero', 'ppi']

class ProfessorForm(forms.ModelForm):
    class Meta:
        model = Professor
        fields = ['departamento', 'lattes', 'area_atuacao']

class EditalForm(forms.ModelForm):
    class Meta:
        model = Edital
        fields = ['titulo', 'descricao', 'arquivo']

class InscricaoForm(forms.ModelForm):
    class Meta:
        model = Inscricao
        fields = ['documento', 'observacao']

class SelecaoForm(forms.ModelForm):
    class Meta:
        model = Selecao
        fields = ['data_inicio', 'data_fim', 'vagas']
        widgets = {
            'data_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'data_fim': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')

        if data_inicio and data_fim:
            if data_inicio >= data_fim:
                raise forms.ValidationError("A data de término deve ser posterior à data de início")
            
            if data_inicio < timezone.now():
                raise forms.ValidationError("A data de início não pode ser no passado")
        
        return cleaned_data