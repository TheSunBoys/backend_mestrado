from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import google.generativeai as genai
import fitz  
import os
import re
from django.http import JsonResponse, HttpResponse
from .forms import AlunoForm, ArquivoForm
from .models import Aluno, Arquivo
import json
import PyPDF2

with open('key.json', 'r') as f:
    google_api_key = json.load(f)["api_key"]

genai.configure(api_key=google_api_key)

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def home(request):
    return render(request, 'home/home.html')

def cadastro_aluno(request):
    if request.method == 'POST':
        aluno_form = AlunoForm(request.POST)

        if aluno_form.is_valid():
            aluno = aluno_form.save()

            # Processando múltiplos arquivos e tipos
            arquivos = request.FILES.getlist('arquivos[]')
            tipos = request.POST.getlist('tipo[]')

            for arquivo, tipo in zip(arquivos, tipos):
                Arquivo.objects.create(aluno=aluno, tipo=tipo, arquivo=arquivo)

            # Criar o JSON com os dados do aluno e dos arquivos
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
            
            return redirect('home')

    else:
        aluno_form = AlunoForm()

    return render(request, 'home/cadastro.html', {'aluno_form': aluno_form})

def deletar_aluno(request, aluno_id):
    # Busca o aluno pelo ID (caso o aluno não exista, retorna erro 404)
    aluno = get_object_or_404(Aluno, pk=aluno_id)

    if request.method == 'POST':
        # Excluir os arquivos relacionados ao aluno
        aluno.arquivos.all().delete()
        
        # Excluir o aluno
        aluno.delete()

        # Exibir mensagem de sucesso
        messages.success(request, f'Aluno {aluno.nome} deletado com sucesso.')

        # Redirecionar para a página da área do professor
        return redirect('area_professor')

    return render(request, 'home/confirmar_deletar.html', {'aluno': aluno})

def area_professor(request):
    alunos = Aluno.objects.all()

    return render(request, 'home/area_professor.html', {'alunos': alunos})

def verificador_de_documento(request):
    if request.method == 'POST':
        body = json.loads(request.body)

        analise_resultados = []

        for aluno in body:
            aluno_id = aluno['aluno_id']
            arquivos = aluno['arquivos'] 
            print(arquivos)

            prompt_para_ia = []
            prompt = "resuma cada um destes arquivos e me retorne um resumo geral sobre o aluno"

            for arquivo in arquivos:
                nome_arquivo = arquivo['nome']
                print(nome_arquivo)
                sample_file = extract_text_from_pdf(nome_arquivo)
                prompt_para_ia.append(sample_file)
            
            prompt_para_ia.insert(0, prompt)

            response = model.generate_content(prompt_para_ia)
            try:
                aluno_obj = Aluno.objects.get(pk=aluno_id)

                analise_resultados.append({
                    'aluno': aluno_obj.nome,
                    'resumo': response.text
                })
            except Aluno.DoesNotExist:
                analise_resultados.append({
                    'aluno': f"ID {aluno_id}",
                    'erro': "Aluno não encontrado"
                })

        resumos = "\n".join([resultado['resumo'] for resultado in analise_resultados if 'resumo' in resultado])

        # Retorna apenas o texto como resposta
        return HttpResponse(resumos, content_type="text/plain")


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