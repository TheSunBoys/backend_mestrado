from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import JsonResponse
from .models import (
    Usuario, 
    Aluno, 
    Professor, 
    Edital, 
    Selecao, 
    Inscricao, 
    AvaliacaoFase,
    Fase
)
from .forms import (
    UsuarioForm, 
    AlunoForm, 
    ProfessorForm,
    EditalForm, 
    InscricaoForm,
    SelecaoForm,
    FaseForm,
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
    print("Iniciando a criação de seleção...")
    edital = get_object_or_404(Edital, pk=edital_id)
    print(f"Edital encontrado: {edital}")

    if request.method == 'POST':
        print("Método POST recebido.")
        form = SelecaoForm(request.POST)
        print(f"Dados do formulário de seleção: {form.data}")
        quantidade_fases = int(request.POST.get('quantidade_fases', 0))
        print(f"Quantidade de fases recebida: {quantidade_fases}")
        
        fase_forms = [FaseForm(request.POST, prefix=f"fase-{x + 1}") for x in range(quantidade_fases)]
        print(f"Formulários de fases criados: {len(fase_forms)}")

        if form.is_valid():
            print("Formulário de seleção válido.")
        else:
            print(f"Erros no formulário de seleção: {form.errors}")

        if all(f.is_valid() for f in fase_forms):
            print("Todos os formulários de fases são válidos.")
        else:
            for i, fase_form in enumerate(fase_forms):
                if not fase_form.is_valid():
                    print(f"Erros no formulário da fase {i + 1}: {fase_form.errors}")

        if form.is_valid() and all(f.is_valid() for f in fase_forms):
            selecao = form.save(commit=False)
            selecao.edital = edital
            selecao.professor_responsavel = request.user
            selecao.save()
            print(f"Seleção criada: {selecao}")

            for i, fase_form in enumerate(fase_forms):
                fase = fase_form.save(commit=False)
                fase.selecao = selecao
                fase.ordem = i + 1
                fase.save()
                print(f"Fase {i + 1} criada: {fase}")
            
            messages.success(request, 'Seleção criada com sucesso!')
            print("Seleção e fases criadas com sucesso.")
            return redirect('exibir_edital', pk=edital.id)
        else:
            print("Erro na validação dos formulários.")

    else:
        print("Método GET recebido.")
        form = SelecaoForm()
        fase_forms = []

    print("Renderizando o template de criação de seleção.")
    return render(request, 'home/selecoes/criar.html', {
        'form': form,
        'fase_forms': fase_forms,
        'edital': edital
    })

def get_fase_form(request):
    """Retorna um formulário de fase para ser usado com HTMX"""
    quantidade_fases = int(request.GET.get('quantidade_fases', 1))
    fase_forms = [FaseForm(prefix=str(x)) for x in range(quantidade_fases)]
    return render(request, 'home/templates/home/selecoes/fase_form.html', {'fase_forms': fase_forms})

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
    
    # Verifica se o usuário já está inscrito
    ja_inscrito = False
    if request.user.is_authenticated and request.user.tipo_usuario == 'aluno':
        ja_inscrito = inscricoes.filter(aluno=request.user).exists()
    
    return render(request, 'home/selecoes/exibir.html', {
        'selecao': selecao,
        'inscricoes': inscricoes,
        'ja_inscrito': ja_inscrito,
        'pode_inscrever': True, #pode_inscrever,
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
    
    if request.user != inscricao.selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para avaliar esta inscrição.')
        return redirect('detalhes_selecao', pk=inscricao.selecao.id)
    
    fase_atual = inscricao.get_fase_atual()
    
    if request.method == 'POST':
        nota = request.POST.get('nota')
        aprovado = request.POST.get('aprovado') == 'on'
        observacoes = request.POST.get('observacoes', '')
        
        avaliacao, created = AvaliacaoFase.objects.update_or_create(
            fase=fase_atual,
            inscricao=inscricao,
            avaliador=request.user,
            defaults={
                'nota': nota,
                'aprovado': aprovado,
                'observacoes': observacoes,
            }
        )
        
        if aprovado:
            tem_proxima_fase = inscricao.avancar_fase()
            if tem_proxima_fase:
                messages.success(request, f'Aluno aprovado na fase {fase_atual.ordem}. Próxima fase: {inscricao.fase_atual}')
            else:
                messages.success(request, 'Aluno aprovado em todas as fases!')
        else:
            inscricao.reprovar()
            messages.warning(request, 'Aluno reprovado na fase atual.')
        
        return redirect('detalhes_selecao', pk=inscricao.selecao.id)
    
    try:
        avaliacao_existente = AvaliacaoFase.objects.get(
            fase=fase_atual,
            inscricao=inscricao,
            avaliador=request.user
        )
    except AvaliacaoFase.DoesNotExist:
        avaliacao_existente = None
    
    context = {
        'inscricao': inscricao,
        'fase_atual': fase_atual,
        'avaliacao_existente': avaliacao_existente,
    }
    
    return render(request, 'home/inscricoes/avaliar.html', context)

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'professor')
def avaliar_fase(request, selecao_id):
    selecao = get_object_or_404(Selecao, id=selecao_id)
    print(f"Seleção encontrada: {selecao}")
    print(f"Fases da seleção: {selecao.fases_selecao.all()}")

    fase = selecao.fases_selecao.filter(status='atual').first()
    print(f"Fase atual encontrada: {fase}")
    if fase:
        print(f"Detalhes da fase atual: ID={fase.id}, Ordem={fase.ordem}, Tipo={fase.tipo_fase}, Nota de Corte={fase.nota_corte}, Status={fase.status}")
    else:
        print("Nenhuma fase atual encontrada.")
    
    inscricoes = selecao.inscricoes.all()
    print(f"Inscrições encontradas: {inscricoes}")

    # Prepara as avaliações para o template
    inscricoes_com_avaliacoes = []
    for inscricao in inscricoes:
        avaliacao = inscricao.avaliacoes_fases.filter(fase=fase).first()
        inscricoes_com_avaliacoes.append({
            'inscricao': inscricao,
            'avaliacao': avaliacao
        })

    if request.method == 'POST':
        # Lógica para salvar as avaliações
        for item in inscricoes_com_avaliacoes:
            inscricao = item['inscricao']
            nota = request.POST.get(f'nota_{inscricao.id}')
            if nota:
                nota = float(nota)
                avaliacao = item['avaliacao']
                if not avaliacao:
                    # Cria uma nova avaliação se não existir
                    avaliacao = AvaliacaoFase.objects.create(
                        fase=fase,
                        inscricao=inscricao,
                        nota=nota,
                        aprovado=(nota >= fase.nota_corte if fase.tipo_fase == 'eliminatoria' else True)
                    )
                else:
                    # Atualiza a avaliação existente
                    avaliacao.nota = nota
                    avaliacao.aprovado = (nota >= fase.nota_corte if fase.tipo_fase == 'eliminatoria' else True)
                    avaliacao.save()

        messages.success(request, 'Avaliações salvas com sucesso!')
        return redirect('detalhes_selecao', pk=selecao_id)

    return render(request, 'home/selecoes/avaliar_fase.html', {
        'selecao': selecao,
        'fase': fase,
        'inscricoes_com_avaliacoes': inscricoes_com_avaliacoes
    })

@login_required
@user_passes_test(is_professor)
def iniciar_fase(request, selecao_id, fase_id):
    selecao = get_object_or_404(Selecao, pk=selecao_id)
    fase = get_object_or_404(Fase, pk=fase_id, selecao=selecao)
    
    # Verifica se o usuário tem permissão
    if request.user != selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para iniciar esta fase.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    # Verifica se a fase pode ser iniciada
    if fase.ordem != selecao.fase_atual:
        messages.error(request, 'Você só pode iniciar a fase atual em sequência.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    if fase.status != 'não iniciada':
        messages.error(request, 'Esta fase já foi iniciada ou finalizada.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    # Verifica se a fase anterior foi finalizada (exceto para a primeira fase)
    if fase.ordem > 1:
        fase_anterior = selecao.fases_selecao.get(ordem=fase.ordem-1)
        if fase_anterior.status != 'finalizada':
            messages.error(request, 'Você precisa finalizar a fase anterior antes de iniciar esta.')
            return redirect('detalhes_selecao', pk=selecao_id)
    
    # Inicia a fase
    fase.status = 'atual'
    fase.save()
    
    messages.success(request, f'Fase {fase.ordem} iniciada com sucesso!')
    return redirect('detalhes_selecao', pk=selecao_id)

@login_required
@user_passes_test(is_professor)
def finalizar_fase(request, selecao_id, fase_id):
    selecao = get_object_or_404(Selecao, pk=selecao_id)
    fase = get_object_or_404(Fase, pk=fase_id, selecao=selecao)
    
    # Verifica se o usuário tem permissão
    if request.user != selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para finalizar esta fase.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    # Verifica se a fase pode ser finalizada
    if fase.status != 'atual':
        messages.error(request, 'Esta fase não está ativa para ser finalizada.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    # Finaliza a fase
    fase.status = 'finalizada'
    fase.save()
    
    # Avança para a próxima fase se houver
    if selecao.fase_atual < selecao.quantidade_fases:
        selecao.fase_atual += 1
        selecao.save()
        
        # Atualiza a próxima fase para "não iniciada"
        try:
            proxima_fase = selecao.fases_selecao.get(ordem=selecao.fase_atual)
            proxima_fase.status = 'não iniciada'
            proxima_fase.save()
        except Fase.DoesNotExist:
            pass
    
    messages.success(request, f'Fase {fase.ordem} finalizada com sucesso!')
    return redirect('detalhes_selecao', pk=selecao_id)

@login_required
@user_passes_test(is_professor)
def avaliar_inscricoes_massa(request, selecao_id):
    """Avaliação em massa de inscrições por professores"""
    selecao = get_object_or_404(Selecao, pk=selecao_id)
    inscricoes = selecao.inscricoes.all()

    if request.method == 'POST':
        fase_atual = selecao.fases_selecao.first()  # Considerando a primeira fase para simplificação
        for inscricao in inscricoes:
            nota = request.POST.get(f'nota_{inscricao.id}')
            aprovado = request.POST.get(f'aprovado_{inscricao.id}') == 'on'
            if nota:
                # Atualiza a avaliação da fase
                avaliacao, created = AvaliacaoFase.objects.update_or_create(
                    fase=fase_atual,
                    inscricao=inscricao,
                    avaliador=request.user,
                    defaults={
                        'nota': nota,
                        'aprovado': aprovado,
                    }
                )
                
                # Lógica de aprovação e reprovação
                if fase_atual.tipo_fase == 'classificatoria':
                    if inscricao.inscricoes.count() < fase_atual.numero_vagas:  # Verifica se a nota está dentro do número de vagas
                        inscricao.avancar_fase()
                elif fase_atual.tipo_fase == 'eliminatoria':
                    if float(nota) >= fase_atual.nota_corte:  # Verifica se a nota está acima da nota de corte
                        inscricao.avancar_fase()
                    else:
                        inscricao.reprovar()

        messages.success(request, 'Avaliações atualizadas com sucesso!')
        return redirect('detalhes_selecao', pk=selecao.id)

    return render(request, 'home/inscricoes/avaliar_massa.html', {
        'selecao': selecao,
        'inscricoes': inscricoes,
    })

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
    editais_recentes = Edital.objects.filter(ativo=True).order_by('-data_publicacao')[:5]
    return render(request, 'home/pagina_edital.html', {'editais_recentes': editais_recentes})

def blog(request):
    return render(request, 'home/blog.html')

