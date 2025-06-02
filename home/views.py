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
    Fase,
    ValorCampoFase,
    TipoCampo,
    CampoFase
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

def registrar_usuario(request):
    """Registro de novos usuários"""
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            login(request, user)
            if user.tipo_usuario == 'aluno':
                return redirect('completar_perfil_aluno')
            elif user.tipo_usuario == 'professor':
                return redirect('completar_perfil_professor')
            return redirect('home')
    else:
        form = UsuarioForm()
    
    return render(request, 'home/registro.html', {'form': form})

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

@login_required
@user_passes_test(is_professor)
def criar_selecao(request, edital_id):
    """Cria uma seleção associada a um edital"""
    edital = get_object_or_404(Edital, pk=edital_id)

    if request.method == 'POST':
        form = SelecaoForm(request.POST)
        quantidade_fases = int(request.POST.get('quantidade_fases', 0))
        
        fase_forms = [FaseForm(request.POST, prefix=f"fase-{x + 1}") for x in range(quantidade_fases)]

        if form.is_valid() and all(f.is_valid() for f in fase_forms):
            selecao = form.save(commit=False)
            selecao.edital = edital
            selecao.professor_responsavel = request.user
            selecao.save()

            for i, fase_form in enumerate(fase_forms):
                fase = fase_form.save(commit=False)
                fase.selecao = selecao
                fase.ordem = i + 1
                fase.save()
            
            messages.success(request, 'Seleção criada com sucesso!')
            return redirect('exibir_edital', pk=edital.id)
        else:
            print("Erro na validação dos formulários.")

    else:
        form = SelecaoForm()
        fase_forms = []

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
    selecao = get_object_or_404(Selecao, pk=pk)
    if request.user != selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para editar esta seleção.')
        return redirect('detalhes_selecao', pk=selecao.id)

    if request.method == 'POST':
        form = SelecaoForm(request.POST, instance=selecao)
        fases = selecao.fases_selecao.all().order_by('ordem')
        fase_forms = [FaseForm(request.POST, prefix=f"fase-{i+1}", instance=fase) for i, fase in enumerate(fases)]

        # Processa as fases já existentes normalmente
        if form.is_valid() and all(f.is_valid() for f in fase_forms):
            selecao = form.save()
            for i, fase_form in enumerate(fase_forms):
                fase = fase_form.save(commit=False)
                fase.selecao = selecao
                fase.ordem = i + 1
                fase.save()

            # Processa as novas fases adicionadas dinamicamente
            nova_fase_count = 1
            while True:
                nome = request.POST.get(f'nova_fase_nome_{nova_fase_count}')
                print(f"Processando nova fase {nova_fase_count}: nome={nome}")
                if not nome:
                    print(f"Parando processamento de novas fases em nova_fase_count={nova_fase_count} (nome vazio ou não encontrado)")
                    break  # Não há mais novas fases
                descricao = request.POST.get(f'nova_fase_descricao_{nova_fase_count}', '')
                tipo_fase = request.POST.get(f'nova_fase_tipo_{nova_fase_count}')
                numero_vagas = request.POST.get(f'nova_fase_numero_vagas_{nova_fase_count}') or None
                nota_corte = request.POST.get(f'nova_fase_nota_corte_{nova_fase_count}') or None
                data_inicio = request.POST.get(f'nova_fase_data_inicio_{nova_fase_count}')
                data_fim = request.POST.get(f'nova_fase_data_fim_{nova_fase_count}')
                peso = request.POST.get(f'nova_fase_peso_{nova_fase_count}')

                print(
                    f"Nova fase {nova_fase_count} - nome: {nome}, descricao: {descricao}, tipo_fase: {tipo_fase}, "
                    f"numero_vagas: {numero_vagas}, nota_corte: {nota_corte}, data_inicio: {data_inicio}, "
                    f"data_fim: {data_fim}, peso: {peso}"
                )

                try:
                    Fase.objects.create(
                        selecao=selecao,
                        nome=nome,
                        descricao=descricao,
                        tipo_fase=tipo_fase,
                        numero_vagas=numero_vagas if tipo_fase == 'classificatoria' else None,
                        nota_corte=nota_corte if tipo_fase == 'eliminatoria' else None,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        peso=peso,
                        ordem=fases.count() + nova_fase_count
                    )
                    print(f"Nova fase {nova_fase_count} criada com sucesso.")
                except Exception as e:
                    print(f"Erro ao criar nova fase {nova_fase_count}: {e}")

                nova_fase_count += 1

            messages.success(request, 'Seleção atualizada com sucesso!')
            return redirect('detalhes_selecao', pk=selecao.id)
        else:
            print("Formulário principal ou de fases inválido.")
            print(f"Erros do form: {form.errors}")
            for idx, f in enumerate(fase_forms):
                print(f"Erros do fase_form {idx+1}: {f.errors}")
    else:
        form = SelecaoForm(instance=selecao)
        fases = selecao.fases_selecao.all().order_by('ordem')
        fase_forms = [FaseForm(instance=fase, prefix=f"fase-{i+1}") for i, fase in enumerate(fases)]

    return render(request, 'home/selecoes/editar.html', {
        'form': form,
        'fase_forms': fase_forms,
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
    
    ja_inscrito = False
    if request.user.is_authenticated and request.user.tipo_usuario == 'aluno':
        ja_inscrito = inscricoes.filter(aluno=request.user).exists()
    
    return render(request, 'home/selecoes/exibir.html', {
        'selecao': selecao,
        'inscricoes': inscricoes,
        'ja_inscrito': ja_inscrito,
        'pode_inscrever': True, #remover essa linha
        'now': timezone.now()
    })

@login_required
@user_passes_test(is_aluno)
def inscrever_selecao(request, pk):
    """Inscrição em seleção por alunos"""
    selecao = get_object_or_404(Selecao, pk=pk)
    ja_inscrito = Inscricao.objects.filter(aluno=request.user, selecao=selecao).exists()
    
    if ja_inscrito:
        messages.error(request, "Inscrição não permitida")
        return redirect('detalhes_selecao', pk=pk)
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
    fase = selecao.fases_selecao.filter(status='atual').first()
    inscricoes = selecao.inscricoes.all()

    inscricoes_com_avaliacoes = []
    for inscricao in inscricoes:
        avaliacao = inscricao.avaliacoes_fases.filter(fase=fase).first()
        status_por_fase = inscricao.get_status_por_fase()
        
        inscricoes_com_avaliacoes.append({
            'inscricao': inscricao,
            'avaliacao': avaliacao,
            'status_por_fase': status_por_fase
        })

    if request.method == 'POST':
        for item in inscricoes_com_avaliacoes:
            inscricao = item['inscricao']
            nota = request.POST.get(f'nota_{inscricao.id}')
            if nota:
                nota = float(nota)
                avaliacao = item['avaliacao']
                if not avaliacao:
                    avaliacao = AvaliacaoFase.objects.create(
                        fase=fase,
                        inscricao=inscricao,
                        nota=nota,
                        aprovado=(nota >= fase.nota_corte if fase.tipo_fase == 'eliminatoria' else True)
                    )
                else:
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
    
    if request.user != selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para iniciar esta fase.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    if fase.ordem != selecao.fase_atual:
        messages.error(request, 'Você só pode iniciar a fase atual em sequência.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    if fase.status != 'não iniciada':
        messages.error(request, 'Esta fase já foi iniciada ou finalizada.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    if fase.ordem > 1:
        fase_anterior = selecao.fases_selecao.get(ordem=fase.ordem-1)
        if fase_anterior.status != 'finalizada':
            messages.error(request, 'Você precisa finalizar a fase anterior antes de iniciar esta.')
            return redirect('detalhes_selecao', pk=selecao_id)
    
    fase.status = 'atual'
    fase.save()
    
    messages.success(request, f'Fase {fase.ordem} iniciada com sucesso!')
    return redirect('detalhes_selecao', pk=selecao_id)

@login_required
@user_passes_test(is_professor)
def finalizar_fase(request, selecao_id, fase_id):
    selecao = get_object_or_404(Selecao, pk=selecao_id)
    fase = get_object_or_404(Fase, pk=fase_id, selecao=selecao)
    
    if request.user != selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para finalizar esta fase.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    if fase.status != 'atual':
        messages.error(request, 'Esta fase não está ativa para ser finalizada.')
        return redirect('detalhes_selecao', pk=selecao_id)
    
    inscricoes_na_fase = selecao.inscricoes.filter(fase_atual=fase.ordem)
    for inscricao in inscricoes_na_fase:
        if not inscricao.avaliacoes_fases.filter(fase=fase).exists():
            messages.error(request, f'A inscrição de {inscricao.aluno.get_full_name()} não foi avaliada!')
            return redirect('detalhes_selecao', pk=selecao_id)
    
    fase.status = 'finalizada'
    fase.save()
    
    for inscricao in inscricoes_na_fase:
        avaliacao = inscricao.avaliacoes_fases.filter(fase=fase).first()
        if not avaliacao.aprovado:
            inscricao.reprovar()

    if selecao.fase_atual < selecao.quantidade_fases:
        selecao.fase_atual += 1
        selecao.save()
        
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
        fase_atual = selecao.fases_selecao.first()
        for inscricao in inscricoes:
            nota = request.POST.get(f'nota_{inscricao.id}')
            aprovado = request.POST.get(f'aprovado_{inscricao.id}') == 'on'
            if nota:
                avaliacao, created = AvaliacaoFase.objects.update_or_create(
                    fase=fase_atual,
                    inscricao=inscricao,
                    avaliador=request.user,
                    defaults={
                        'nota': nota,
                        'aprovado': aprovado,
                    }
                )
                
                if fase_atual.tipo_fase == 'classificatoria':
                    if inscricao.inscricoes.count() < fase_atual.numero_vagas:
                        inscricao.avancar_fase()
                elif fase_atual.tipo_fase == 'eliminatoria':
                    if float(nota) >= fase_atual.nota_corte:
                        inscricao.avancar_fase()
                    else:
                        inscricao.reprovar()

        messages.success(request, 'Avaliações atualizadas com sucesso!')
        return redirect('detalhes_selecao', pk=selecao.id)

    return render(request, 'home/inscricoes/avaliar_massa.html', {
        'selecao': selecao,
        'inscricoes': inscricoes,
    })

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

@login_required
@user_passes_test(is_professor)
def gerenciar_campos_fase(request, fase_id):
    fase = get_object_or_404(Fase, pk=fase_id)
    campos = fase.campos.all().order_by('ordem')
    
    if request.user != fase.selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para gerenciar esta fase.')
        return redirect('detalhes_selecao', pk=fase.selecao.id)
    
    return render(request, 'home/fases/gerenciar_campos.html', {
        'fase': fase,
        'campos': campos
    })

@login_required
@user_passes_test(is_professor)
def adicionar_campo_fase(request, fase_id):
    fase = get_object_or_404(Fase, pk=fase_id)
    
    if request.user != fase.selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para adicionar campos nesta fase.')
        return redirect('gerenciar_campos_fase', fase_id=fase_id)
    
    if request.method == 'POST':
        tipo_campo_id = request.POST.get('tipo_campo')
        tipo_campo = get_object_or_404(TipoCampo, pk=tipo_campo_id)
        
        campo = CampoFase(
            fase=fase,
            tipo=tipo_campo,
            nome=request.POST.get('nome'),
            descricao=request.POST.get('descricao', ''),
            obrigatorio=request.POST.get('obrigatorio') == 'on',
            ordem=request.POST.get('ordem', 1),
            peso=request.POST.get('peso', 1.0)
        )
        campo.save()
        messages.success(request, 'Campo adicionado com sucesso!')
        return redirect('gerenciar_campos_fase', fase_id=fase_id)
    
    tipos_campo = TipoCampo.objects.all()
    return render(request, 'home/fases/adicionar_campo.html', {
        'fase': fase,
        'tipos_campo': tipos_campo
    })

@login_required
@user_passes_test(is_professor)
def editar_campo_fase(request, campo_id):
    campo = get_object_or_404(CampoFase, pk=campo_id)
    
    if request.user != campo.fase.selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para editar este campo.')
        return redirect('gerenciar_campos_fase', fase_id=campo.fase.id)
    
    if request.method == 'POST':
        campo.nome = request.POST.get('nome')
        campo.descricao = request.POST.get('descricao', '')
        campo.obrigatorio = request.POST.get('obrigatorio') == 'on'
        campo.ordem = request.POST.get('ordem', 1)
        campo.peso = request.POST.get('peso', 1.0)
        campo.save()
        messages.success(request, 'Campo atualizado com sucesso!')
        return redirect('gerenciar_campos_fase', fase_id=campo.fase.id)
    
    return render(request, 'home/fases/editar_campo.html', {
        'campo': campo
    })

@login_required
@user_passes_test(is_professor)
def excluir_campo_fase(request, campo_id):
    campo = get_object_or_404(CampoFase, pk=campo_id)
    fase_id = campo.fase.id
    
    if request.user != campo.fase.selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para excluir este campo.')
        return redirect('gerenciar_campos_fase', fase_id=fase_id)
    
    campo.delete()
    messages.success(request, 'Campo excluído com sucesso!')
    return redirect('gerenciar_campos_fase', fase_id=fase_id)

@login_required
@user_passes_test(is_aluno)
def responder_fase(request, fase_id):
    fase = get_object_or_404(Fase, pk=fase_id)
    inscricao = get_object_or_404(Inscricao, selecao=fase.selecao, aluno=request.user)
    
    if fase.status != 'atual' or inscricao.fase_atual != fase.ordem:
        messages.error(request, 'Você não pode responder esta fase no momento.')
        return redirect('detalhes_selecao', pk=fase.selecao.id)
    
    campos = fase.campos.all().order_by('ordem')
    
    if request.method == 'POST':
        for campo in campos:
            valor = request.POST.get(f'campo_{campo.id}')
            arquivo = request.FILES.get(f'arquivo_{campo.id}')
            
            ValorCampoFase.objects.update_or_create(
                campo=campo,
                inscricao=inscricao,
                defaults={
                    'valor_texto': valor if campo.tipo.tipo_dado in ['texto', 'escolha', 'multipla'] else None,
                    'valor_numero': valor if campo.tipo.tipo_dado == 'numero' else None,
                    'valor_data': valor if campo.tipo.tipo_dado == 'data' else None,
                    'valor_arquivo': arquivo if campo.tipo.tipo_dado == 'arquivo' else None,
                    'valor_booleano': valor == 'on' if campo.tipo.tipo_dado == 'booleano' else None,
                }
            )
        
        messages.success(request, 'Respostas enviadas com sucesso!')
        return redirect('detalhes_selecao', pk=fase.selecao.id)
    
    valores = {v.campo.id: v for v in inscricao.valores_campos.filter(campo__in=campos)}
    
    return render(request, 'home/fases/responder.html', {
        'fase': fase,
        'campos': campos,
        'valores': valores
    })

@login_required
@user_passes_test(is_professor)
def ver_respostas_fase(request, fase_id):
    fase = get_object_or_404(Fase, pk=fase_id)
    
    if request.user != fase.selecao.professor_responsavel and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para ver estas respostas.')
        return redirect('detalhes_selecao', pk=fase.selecao.id)
    
    inscricoes = fase.selecao.inscricoes.filter(fase_atual__gte=fase.ordem)
    campos = fase.campos.all().order_by('ordem')
    
    # Estrutura para armazenar todas as respostas
    respostas = []
    for inscricao in inscricoes:
        resposta = {
            'inscricao': inscricao,
            'valores': {}
        }
        for campo in campos:
            try:
                valor = inscricao.valores_campos.get(campo=campo)
                resposta['valores'][campo.id] = valor.get_valor()
            except ValorCampoFase.DoesNotExist:
                resposta['valores'][campo.id] = None
        respostas.append(resposta)
    
    return render(request, 'home/fases/respostas.html', {
        'fase': fase,
        'campos': campos,
        'respostas': respostas
    })

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

