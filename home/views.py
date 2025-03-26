from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from google import genai
from django.http import JsonResponse, HttpResponse
from .forms import AlunoForm, ArquivoForm
from .models import Aluno, Arquivo
import json
import PyPDF2
from django.contrib.auth.decorators import login_required
from .models import Edital, Selecao
from .forms import EditalForm, InscricaoForm

with open('key.json', 'r') as f:
    google_api_key = json.load(f)["api_key"]

client = genai.Client(api_key=google_api_key)

@login_required
def dashboard(request):
    return render(request, 'home/dashboard.html')

def home(request):
    return render(request, 'home/home.html')

def cadastro_aluno(request):
    if request.method == 'POST':
        aluno_form = AlunoForm(request.POST)

        if aluno_form.is_valid():
            aluno = aluno_form.save()

            arquivos = request.FILES.getlist('arquivos[]')
            tipos = request.POST.getlist('tipo[]')

            for arquivo, tipo in zip(arquivos, tipos):
                Arquivo.objects.create(aluno=aluno, tipo=tipo, arquivo=arquivo)

            aluno_json = {
                'nome': aluno.nome,
                'idade': aluno.idade,
                'curso': aluno.curso,
                'ira': aluno.ira,
                'email': aluno.email,
                'lattes': aluno.lattes,
                'github': aluno.github,
                'interesse': aluno.interesse,
                'genero': aluno.genero,
                'ppi': aluno.ppi,
                'cpf': aluno.cpf,
                'arquivos': [{'tipo': arq.tipo, 'url': arq.arquivo.url} for arq in aluno.arquivos.all()],
                'data_cadastro': aluno.data_cadastro.isoformat(),
            }

            print("Dados do Aluno:", aluno_json)
            
            return redirect('home')

    else:
        aluno_form = AlunoForm()

    return render(request, 'home/cadastro.html', {'aluno_form': aluno_form})

def deletar_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, pk=aluno_id)

    if request.method == 'POST':
        aluno.arquivos.all().delete()
        aluno.delete()
        messages.success(request, f'Aluno {aluno.nome} deletado com sucesso.')
        return redirect('area_professor')

    return render(request, 'home/confirmar_deletar.html', {'aluno': aluno})

def area_professor(request):
    alunos = Aluno.objects.all()

    return render(request, 'home/area_professor.html', {'alunos': alunos})

def verificador_de_documento(request):
    if request.method == 'POST':
        body = json.loads(request.body)

        analise_individual = []

        for aluno in body:
            arquivos = aluno['arquivos']
            
            prompt_para_ia = []
            prompt = f"Fale um pouco sobre cada arquivo deste aluno e dê uma nota profissional."

            for arquivo in arquivos:
                nome_arquivo = arquivo['nome']
                print(f"Lendo o arquivo: {nome_arquivo}")
                sample_file = extract_text_from_pdf(nome_arquivo)
                prompt_para_ia.append(sample_file)

            prompt_para_ia.insert(0, prompt)
            
            response = client.models.generate_content(model="gemini-1.5-flash",
                                                      contents=prompt_para_ia)
            
            analise_individual.append(response.text)

        print("Resultados Individuais:", analise_individual)
        prompt_comparativo = "Se comporte como um professor de mestrado avaliando perfis de alunos. Compare os seguintes alunos com base em seus resumos e dê um ranking:"
        comparativo_para_ia = [prompt_comparativo]
        
        for analise in analise_individual:
            comparativo_para_ia.append(f"{analise}")

        response_comparativo = client.models.generate_content(model="gemini-1.5-flash",
                                                              contents=comparativo_para_ia)
        return render(request, 'parcial/resultado.html', {'analise_resultados': response_comparativo.text })

    else: 
        alunos = Aluno.objects.all()
        return render(request, 'home/avaliar.html', {'alunos': alunos})

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text
        return extracted_text

def index(request):
    editais = Edital.objects.filter(ativo=True).order_by('-data_publicacao')
    return render(request, 'editais/index.html', {'editais': editais})

def criar_edital(request):
    if request.method == 'POST':
        form = EditalForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index_editais')
    else:
        form = EditalForm()
    return render(request, 'editais/criar.html', {'form': form})

def editar_edital(request, id):
    edital = get_object_or_404(Edital, pk=id)
    if request.method == 'POST':
        form = EditalForm(request.POST, request.FILES, instance=edital)
        if form.is_valid():
            form.save()
            return redirect('index_editais')
    else:
        form = EditalForm(instance=edital)
    return render(request, 'editais/editar.html', {'form': form})

def deletar_edital(request, id):
    edital = get_object_or_404(Edital, pk=id)
    edital.ativo = False
    edital.save()
    return redirect('index_editais')

@login_required
def inscrever_selecao(request, selecao_id):
    selecao = get_object_or_404(Selecao, id=selecao_id)
    
    if request.method == 'POST':
        form = InscricaoForm(request.POST, request.FILES)
        if form.is_valid():
            inscricao = form.save(commit=False)
            inscricao.aluno = request.user
            inscricao.selecao = selecao
            inscricao.save()
            return redirect('detalhes_selecao', selecao_id=selecao.id)
    else:
        form = InscricaoForm()
    
    return render(request, 'inscricao/formulario.html', {
        'form': form,
        'selecao': selecao
    })