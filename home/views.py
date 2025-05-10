from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import JsonResponse
from .models import Usuario, Aluno, Professor, Edital, Selecao, Inscricao
from .forms import (
    UsuarioForm, 
    AlunoForm, 
    ProfessorForm,
    EditalForm, 
    InscricaoForm,
    SelecaoForm,
)
import json
from google import genai
import PyPDF2

with open('key.json', 'r') as f:
    google_api_key = json.load(f)["api_key"]

client = genai.Client(api_key=google_api_key)

def is_aluno(user):
    return user.tipo_usuario == 'aluno'

def is_professor(user):
    return user.tipo_usuario == 'professor'

def is_admin(user):
    return user.is_superuser or user.tipo_usuario == 'admin'

def custom_logout(request):
    request.session.flush()
    logout(request)
    return redirect('login')

def home(request):
    """Página inicial pública"""
    editais_recentes = Edital.objects.filter(ativo=True).order_by('-data_publicacao')[:5]
    
    return render(request, 'home/home.html', {'editais_recentes': editais_recentes})

# --- Views de Autenticação ---
def registrar_usuario(request):
    """Registro de novos usuários"""
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Login automático e redirecionamento
            login(request, user)
            if user.tipo_usuario == 'aluno':
                return redirect('completar_perfil_aluno')
            elif user.tipo_usuario == 'professor':
                return redirect('completar_perfil_professor')
            return redirect('home')
    else:
        form = UsuarioForm()
    
    return render(request, 'home/registro.html', {'form': form})

# --- Views de Perfil ---
@login_required
@user_passes_test(is_aluno)
def completar_perfil_aluno(request):
    """Completar perfil de aluno"""
    try:
        perfil = request.user.perfil_aluno
        form = AlunoForm(request.POST or None, request.FILES or None, instance=perfil)
    except Aluno.DoesNotExist:
        form = AlunoForm(request.POST or None, request.FILES or None)
    
    if request.method == 'POST' and form.is_valid():
        perfil = form.save(commit=False)
        perfil.usuario = request.user
        perfil.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('area_aluno')
    
    return render(request, 'home/completar_perfil_aluno.html', {'form': form})

@login_required
@user_passes_test(is_professor)
def completar_perfil_professor(request):
    """Completar perfil de professor"""
    try:
        perfil = request.user.perfil_professor
        form = ProfessorForm(request.POST or None, instance=perfil)
    except Professor.DoesNotExist:
        form = ProfessorForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        perfil = form.save(commit=False)
        perfil.usuario = request.user
        perfil.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('area_professor')
    
    return render(request, 'home/completar_perfil_professor.html', {'form': form})

# --- Áreas Restritas ---
@login_required
@user_passes_test(is_aluno)
def area_aluno(request):
    """Dashboard do aluno"""
    try:
        perfil = request.user.perfil_aluno
    except Aluno.DoesNotExist:
        return redirect('completar_perfil_aluno')
    
    inscricoes = Inscricao.objects.filter(aluno=request.user).select_related('selecao__edital')
    return render(request, 'home/area_aluno.html', {
        'perfil': perfil,
        'inscricoes': inscricoes
    })

@login_required
@user_passes_test(is_professor)
def area_professor(request):
    """Dashboard do professor"""
    try:
        perfil = request.user.perfil_professor
    except Professor.DoesNotExist:
        return redirect('completar_perfil_professor')
    
    selecoes = Selecao.objects.filter(professor_responsavel=request.user).prefetch_related('inscricoes')
    return render(request, 'home/area_professor.html', {
        'perfil': perfil,
        'selecoes': selecoes
    })

# --- Views de Edital ---
@login_required
def listar_editais(request):
    """Lista todos os editais ativos"""
    editais = Edital.objects.filter(ativo=True).order_by('-data_publicacao')
    return render(request, 'home/editais/listar.html', {'editais': editais})

@login_required
def exibir_edital(request, pk):
    """Exibe os detalhes completos de um edital"""
    edital = get_object_or_404(Edital, pk=pk)
    selecoes = edital.selecoes.all().select_related('professor_responsavel')
    
    # Verifica se o usuário pode criar seleções neste edital
    pode_criar_selecao = (
        request.user.tipo_usuario == 'professor' and 
        (request.user == edital.criado_por or request.user.is_superuser)
    )
    
    context = {
        'edital': edital,
        'selecoes': selecoes,
        'pode_criar_selecao': pode_criar_selecao,
        'now': timezone.now()
    }
    
    return render(request, 'home/editais/exibir.html', context)

@login_required
@user_passes_test(is_professor)
def criar_edital(request):
    """Criação de novo edital"""
    if request.method == 'POST':
        form = EditalForm(request.POST, request.FILES)
        if form.is_valid():
            edital = form.save(commit=False)
            edital.criado_por = request.user
            edital.save()
            messages.success(request, 'Edital criado com sucesso!')
            return redirect('listar_editais')
    else:
        form = EditalForm()
    
    return render(request, 'home/editais/criar.html', {'form': form})

@login_required
@user_passes_test(is_professor)
def editar_edital(request, pk):
    """Edição de edital existente"""
    edital = get_object_or_404(Edital, pk=pk)
    if request.method == 'POST':
        form = EditalForm(request.POST, request.FILES, instance=edital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Edital atualizado com sucesso!')
            return redirect('listar_editais')
    else:
        form = EditalForm(instance=edital)
    
    return render(request, 'home/editais/editar.html', {'form': form, 'edital': edital})

@login_required
@user_passes_test(is_professor)
def excluir_edital(request, pk):
    """Desativa um edital"""
    edital = get_object_or_404(Edital, pk=pk)
    edital.ativo = False
    edital.save()
    messages.success(request, 'Edital desativado com sucesso!')
    return redirect('listar_editais')

# --- Views de Seleção ---
@login_required
@user_passes_test(is_professor)
def criar_selecao(request, edital_id):
    """Cria uma seleção associada a um edital"""
    edital = get_object_or_404(Edital, pk=edital_id)
    print(edital_id)
    if request.method == 'POST':
        form = SelecaoForm(request.POST)
        if form.is_valid():
            selecao = form.save(commit=False)
            selecao.edital = edital
            selecao.professor_responsavel = request.user
            selecao.save()

            messages.success(request, 'Seleção criada com sucesso!')
            return redirect('exibir_edital', pk=edital.id)
    else:
        form = SelecaoForm()
    
    return render(request, 'home/selecoes/criar.html', {
        'form': form,
        'edital': edital
    })

@login_required
@user_passes_test(is_professor)
def editar_selecao(request, pk):
    """Edição de seleção existente"""
    selecao = get_object_or_404(Selecao, pk=pk)
    
    # Verifica se o usuário tem permissão para editar
    if request.user != selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para editar esta seleção.')
        return redirect('detalhes_selecao', pk=selecao.id)
    
    if request.method == 'POST':
        form = SelecaoForm(request.POST, instance=selecao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seleção atualizada com sucesso!')
            return redirect('detalhes_selecao', pk=selecao.id)
    else:
        form = SelecaoForm(instance=selecao)
    
    return render(request, 'home/selecoes/editar.html', {
        'form': form,
        'selecao': selecao,
        'edital': selecao.edital
    })

@login_required
def detalhes_selecao(request, pk):
    selecao = get_object_or_404(Selecao, pk=pk)
    inscricoes = selecao.inscricoes.all()
    
    pode_inscrever = (
        selecao.data_inicio <= timezone.now() <= selecao.data_fim and
        request.user.tipo_usuario == 'aluno' and
        not inscricoes.filter(aluno=request.user).exists()
    )
    
    return render(request, 'home/selecoes/exibir.html', {
        'selecao': selecao,
        'inscricoes': inscricoes,
        'pode_inscrever': pode_inscrever,
        'now': timezone.now()
    })
# --- Views de Inscrição ---
@login_required
@user_passes_test(is_aluno)
def inscrever_selecao(request, pk):
    """Inscrição em seleção por alunos"""
    selecao = get_object_or_404(Selecao, pk=pk)
    ja_inscrito = Inscricao.objects.filter(aluno=request.user, selecao=selecao).exists()
    
    if ja_inscrito: # or not (selecao.data_inicio <= timezone.now() <= selecao.data_fim):
        messages.error(request, "Inscrição não permitida")
        return redirect('detalhes_selecao', pk=pk)
    # Verifica se já está inscrito
    if Inscricao.objects.filter(aluno=request.user, selecao=selecao).exists():
        messages.warning(request, 'Você já está inscrito nesta seleção!')
        return redirect('area_aluno')
    
    if request.method == 'POST':
        form = InscricaoForm(request.POST, request.FILES)
        if form.is_valid():
            inscricao = form.save(commit=False)
            inscricao.aluno = request.user
            inscricao.selecao = selecao
            inscricao.save()
            messages.success(request, 'Inscrição realizada com sucesso!')
            return redirect('area_aluno')
    else:
        form = InscricaoForm()
    
    return render(request, 'home/inscricoes/inscrever.html', {
        'form': form,
        'selecao': selecao
    })

@login_required
@user_passes_test(is_professor)
def avaliar_inscricao(request, inscricao_id):
    """Avaliação de inscrição por professores"""
    inscricao = get_object_or_404(Inscricao, pk=inscricao_id)
    
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        inscricao.status = novo_status
        inscricao.save()
        messages.success(request, 'Avaliação registrada com sucesso!')
        return redirect('detalhes_selecao', selecao_id=inscricao.selecao.id)
    
    return render(request, 'home/inscricoes/avaliar.html', {'inscricao': inscricao})

# --- Views de Documentos ---
def extract_text_from_pdf(pdf_file):
    """Extrai texto de PDF para análise"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

@login_required
@user_passes_test(is_professor)
def analisar_documentos(request):
    """Análise de documentos usando IA"""
    if request.method == 'POST':
        try:
            inscricao_id = request.POST.get('inscricao_id')
            inscricao = get_object_or_404(Inscricao, pk=inscricao_id)
            
            texto_documento = extract_text_from_pdf(inscricao.documento)
            
            prompt = f"""
            Analise este documento de inscrição para mestrado:
            {texto_documento}
            
            Forneça:
            1. Pontos fortes
            2. Pontos fracos
            3. Recomendações para melhoria
            4. Nota de 0-10
            """
            
            response = client.generate_content(
                model="gemini-1.5-flash",
                contents=[prompt]
            )
            
            return JsonResponse({'analise': response.text})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

# --- Views de Administração ---
@login_required
@user_passes_test(is_admin)
def administrar_usuarios(request):
    """Gestão de usuários para administradores"""
    usuarios = Usuario.objects.all().order_by('-date_joined')
    return render(request, 'home/admin/usuarios.html', {'usuarios': usuarios})

@login_required
@user_passes_test(is_admin)
def alterar_tipo_usuario(request, usuario_id):
    """Alteração de tipo de usuário por admin"""
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    
    if request.method == 'POST':
        novo_tipo = request.POST.get('tipo_usuario')
        usuario.tipo_usuario = novo_tipo
        usuario.save()
        
        # Remove perfis antigos se o tipo mudar
        if novo_tipo != 'aluno':
            Aluno.objects.filter(usuario=usuario).delete()
        if novo_tipo != 'professor':
            Professor.objects.filter(usuario=usuario).delete()
        
        messages.success(request, 'Tipo de usuário atualizado com sucesso!')
        return redirect('administrar_usuarios')
    
    return render(request, 'home/admin/alterar_tipo.html', {'usuario': usuario})

def dashboard(request):
    return render(request, 'home/dashboard.html')

def blog(request):
    return render(request, 'home/blog.html')