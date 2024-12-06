from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth.decorators import login_required

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            print("tudo OK")
            return redirect('login') 
        else:
            print("erro ao salvar")
    else:
        print("algo diferente")
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            print("login aceito")
            return redirect('home')  
        else:
            print("sem sucesso")
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def dashboard_view(request):
    if request.user.role == 'teacher':
        return render(request, 'home/home.html')
    elif request.user.role == 'student':
        return render(request, 'home/home.html')
    else:
        return render(request, 'home/home.html')
