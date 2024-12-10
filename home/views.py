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
            # Salva o aluno no banco de dados
            aluno = aluno_form.save()

            # Processa múltiplos arquivos e tipos enviados
            arquivos = request.FILES.getlist('arquivos[]')
            tipos = request.POST.getlist('tipo[]')

            for arquivo, tipo in zip(arquivos, tipos):
                # Cria um registro de arquivo associado ao aluno
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

            print("Dados do Aluno:", aluno_json)  # Exibe no console (opcional)
            
            return redirect('home')  # Redireciona para a página inicial

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

        # Lista para armazenar as análises de cada aluno
        analise_individual = []

        for aluno in body:
            arquivos = aluno['arquivos']
            
            prompt_para_ia = []
            prompt = f"Fale um pouco sobre cada arquivo deste aluno e dê uma nota profissional."

            for arquivo in arquivos:
                nome_arquivo = arquivo['nome']
                print(f"Lendo o arquivo: {nome_arquivo}")
                sample_file = extract_text_from_pdf(nome_arquivo)  # Extração do texto do PDF
                prompt_para_ia.append(sample_file)

            # Insere o prompt inicial para análise individual
            prompt_para_ia.insert(0, prompt)
            
            # Gera a análise individual do aluno
            response = model.generate_content(prompt_para_ia)
            
            # Salva a análise individual com o nome do aluno
            analise_individual.append(response.text)

        print("Resultados Individuais:", analise_individual)

            # Construir o prompt comparativo
        prompt_comparativo = "Se comporte como um professor de mestrado avaliando perfis de alunos. Compare os seguintes alunos com base em seus resumos e dê um ranking:"
        comparativo_para_ia = [prompt_comparativo]
        
            # Adicionar resumos ao prompt comparativo
        for analise in analise_individual:
            comparativo_para_ia.append(f"{analise}")

            # Gera o ranking comparativo
        response_comparativo = model.generate_content(comparativo_para_ia)
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