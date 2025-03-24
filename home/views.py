from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from google import genai
from django.http import JsonResponse, HttpResponse
from .forms import AlunoForm, ArquivoForm
from .models import Aluno, Arquivo
import json
import PyPDF2

with open('key.json', 'r') as f:
    google_api_key = json.load(f)["api_key"]

client = genai.Client(api_key=google_api_key)

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
            ira = aluno.get('ira', None)
            prompt_para_ia = []
            prompt = f"""Você é um avaliador acadêmico real do Processo Seletivo do Mestrado em Ciência da Computação da UFERSA/UERN, portanto irá se portar de formal e técnica.
    Com base no Edital Nº 05/2024 – PPGCC/UERN, avalie o currículo abaixo seguindo rigorosamente os critérios estabelecidos.

    ### **Critérios de Avaliação e Pontuação:**
    1. **Nota de Rendimento Escolar (NRE)** (0 a 10)
       - Índice de Rendimento Acadêmico (IRA) multiplicado pelo CPC do curso.
       - Penalização: egressos de cursos não prioritários recebem apenas 50% da pontuação.

    2. **Nota do Currículo (NC)** (0 a 10) – Somatório dos seguintes itens:
       - Pós-graduação Lato Sensu concluída na área (1.0)
       - Docência:
         - Professor efetivo de IES pública (1.0/semestre)
         - Professor substituto de IES pública ou professor de IES privada (0.75/semestre)
         - Minicurso ministrado (0.2)
       - Experiência profissional em Ciência da Computação (0.5/semestre)
       - Projetos e Estágios:
         - Monitoria/PET/Projeto de Ensino (0.5/semestre)
         - Pesquisa/Iniciação Científica (0.5)
         - Extensão/Estágio voluntário ou remunerado (0.25)
       - Produção Bibliográfica e Técnica:
         - Artigos publicados:
           - Qualis A (2.0)
           - Qualis B (1.0)
           - Qualis C ou sem Qualis (0.5)
         - Resumo Expandido (0.2 com Qualis, 0.1 sem Qualis)
         - Capítulo de livro (0.5), livro completo (1.0)
         - Patente registrada (1.0), concedida (2.0)
         - Registro de software (1.0)
       - POSCOMP: (Percentual de acertos × 3)
       - Disciplinas cursadas no PPgCC: (Nº de créditos × 0.25)

    ### **Informações do Candidato:**
    - **IRA:** {ira}

    ### **Cálculo da Média Final (MF):**
    MP = (NRE * 0.5) + (NC * 0.5)
    MF = (MP * 0.5)


    após os cálculos Agora avalie o currículo abaixo com base nesses critérios, atribua uma **nota de 0 a 10**, forneça essa nota de 0 a 10 na justificativa e forneça uma **justificativa detalhada** explicando os pontos fortes e fracos do candidato e Retorne a nota final e a justificativa da avaliação. lembre-se de avisar para adicionar NAR(nota de arguição oral) a MF(média final)"""

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
