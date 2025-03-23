from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario

class UserRegistrationForm(UserCreationForm):
    cpf = forms.CharField(max_length=11, required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    role = forms.ChoiceField(choices=Usuario.TIPO_USUARIO_CHOICES, required=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'cpf', 'date_of_birth', 'role', 'password1', 'password2']

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}))