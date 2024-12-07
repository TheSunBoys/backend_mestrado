from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import google.generativeai as genai
import fitz  
import os
import re
from django.http import JsonResponse
from .forms import AlunoForm, ArquivoForm
from .models import Aluno, Arquivo
import json
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
    # Busca todos os alunos registrados
    alunos = Aluno.objects.all()

    return render(request, 'home/area_professor.html', {'alunos': alunos})

def verificador_de_documento(request):
    response_data = None 
    fotos = [] 

    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        print("Arquivo PDF recebido:", pdf_file)

        pdf = fitz.open(stream=pdf_file.read(), filetype="pdf")
        print(f"Número de páginas no PDF: {pdf.page_count}")
        output_dir = 'output_images'
        os.makedirs(output_dir, exist_ok=True)

        for page_num in range(pdf.page_count):
            page = pdf.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            image_path = os.path.join(output_dir, f'pagina_{page_num + 1}.png')
            fotos.append(image_path)
            pix.save(image_path)
            print(f'Página {page_num + 1} salva como {image_path}')

        uploaded_files = []
        for foto in fotos:
            print(f"Enviando foto: {foto} para a API Generativa")
            sample_file = genai.upload_file(path=foto, display_name="foto_documento")
            print(sample_file)
            uploaded_files.append(sample_file)

        response_data = model.generate_content([*uploaded_files, "me retorne um json com os dados deste documento"]).text

    
    return render(request, 'home/documento.html', {'response_data': response_data})