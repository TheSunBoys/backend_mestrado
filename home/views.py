from django.shortcuts import render
import google.generativeai as genai
import fitz  
import os
import json
import re
import json 

with open('key.json', 'r') as f:
    google_api_key = json.load(f)["api_key"]

genai.configure(api_key=google_api_key)

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def home(request):
    return render(request, 'home/home.html')

def envio_de_arquivo(request):
    response_data = "penis"
    armazenar_arquivos(request)
    return render(request, 'home/inscricao.html',{'reponse_data': response_data})

def armazenar_arquivos(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        nome_aluno = request.POST.get("nome")
        print("Arquivo PDF recebido:", pdf_file)
        
        output_dir = f'output_images/{nome_aluno}'.strip()
        
        os.makedirs(output_dir, exist_ok=True)
        
        pdf_path = os.path.join(output_dir, f'{pdf_file}') 
        pdf_content = pdf_file.read() 
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content )
        print(f"PDF completo salvo como {pdf_path}")

        dados_pessoais = {
            "nome": nome_aluno
        }

        with open("output_images/{nome_aluno}/dados_pessoais.json", "w", encoding="utf-8") as arquivo_json:
            json.dump(dados_pessoais, arquivo_json, indent=4, ensure_ascii=False)
            
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