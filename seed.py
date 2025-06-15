# seed.py
import os
import django
from django.contrib.auth.hashers import make_password
from faker import Faker

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mestrado.settings')
django.setup()

from home.models import Usuario, Aluno, Professor, Edital, Selecao, Fase, Inscricao, AvaliacaoFase, TipoCampo
from django.utils import timezone

fake = Faker('pt_BR')

def create_tipos_campo():
    tipos = [
        {'nome': 'Texto Linha', 'tipo_dado': 'texto', 'opcoes': ''},
        {'nome': 'Texto Campo', 'tipo_dado': 'texto', 'opcoes': ''},
        {'nome': 'Numérico', 'tipo_dado': 'numero', 'opcoes': ''},
        {'nome': 'Checkbox', 'tipo_dado': 'booleano', 'opcoes': ''},
        {'nome': 'Seleção Única', 'tipo_dado': 'escolha', 'opcoes': 'Excelente\nBom\nRegular\nRuim'},
        {'nome': 'Seleção Múltipla', 'tipo_dado': 'multipla', 'opcoes': 'Python\nJava\nJavaScript\nC++\nOutros'},
        {'nome': 'Data', 'tipo_dado': 'data', 'opcoes': ''},
        {'nome': 'Arquivo', 'tipo_dado': 'arquivo', 'opcoes': ''},
    ]
    
    for tipo in tipos:
        TipoCampo.objects.create(
            nome=tipo['nome'],
            tipo_dado=tipo['tipo_dado'],
            opcoes=tipo['opcoes']
        )
        print(f"Tipo de campo criado: {tipo['nome']} ({tipo['tipo_dado']})")

def create_users():
    alunos = []
    for i in range(1, 11):
        user = Usuario.objects.create(
            username=f'aluno{i}',
            email=f'aluno{i}@example.com',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            cpf=fake.numerify('###########'),
            telefone=fake.numerify('(##) 9####-####'),
            tipo_usuario='aluno',
            password=make_password('123456')
        )
        aluno = Aluno.objects.create(
            usuario=user,
            curso=fake.random_element(['Ciência da Computação', 'Engenharia de Software', 'Sistemas de Informação']),
            ira=fake.pydecimal(left_digits=2, right_digits=2, min_value=5, max_value=10),
            github=f'https://github.com/{user.username}',
            interesse_pesquisa=fake.sentence(),
            genero=fake.random_element(['Masculino', 'Feminino', 'Não binário']),
            ppi=fake.boolean()
        )
        alunos.append(aluno)
        print(f'Aluno criado: {user.get_full_name()}')

    professor_user = Usuario.objects.create(
        username='professor1',
        email='professor1@example.com',
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        cpf=fake.numerify('###########'),
        telefone=fake.numerify('(##) 9####-####'),
        tipo_usuario='professor',
        password=make_password('123456')
    )
    professor = Professor.objects.create(
        usuario=professor_user,
        departamento='Ciência da Computação',
        lattes=f'http://lattes.cnpq.br/{fake.numerify("########")}',
        area_atuacao=fake.sentence()
    )
    print(f'Professor criado: {professor_user.get_full_name()}')

    return alunos, professor

def create_selection(professor):
    edital = Edital.objects.create(
        titulo="Edital de Seleção para Projeto de Pesquisa em IA",
        descricao=fake.text(max_nb_chars=1000),
        arquivo=None,
        criado_por=professor.usuario,
        nota_minima_aprovacao=7.5
    )
    print(f'Edital criado: {edital.titulo}')

    data_inicio = timezone.now()
    data_fim = data_inicio + timezone.timedelta(days=60)
    
    selecao = Selecao.objects.create(
        edital=edital,
        professor_responsavel=professor.usuario,
        data_inicio=data_inicio,
        data_fim=data_fim,
        vagas=3,
        quantidade_fases=5
    )
    print(f'Seleção criada com {selecao.quantidade_fases} fases')

    tipos_fase = ['eliminatoria', 'classificatoria', 'eliminatoria', 'classificatoria', 'eliminatoria']
    for i in range(1, 6):
        fase_inicio = data_inicio + timezone.timedelta(days=(i-1)*10)
        fase_fim = fase_inicio + timezone.timedelta(days=9)
        
        Fase.objects.create(
            selecao=selecao,
            nome=f'Fase {i} - {tipos_fase[i-1].capitalize()}',
            descricao=fake.text(max_nb_chars=200),
            ordem=i,
            data_inicio=fase_inicio,
            data_fim=fase_fim,
            tipo_fase=tipos_fase[i-1],
            peso=0.2 if i < 5 else 0.4, 
            nota_corte=7.0 if tipos_fase[i-1] == 'eliminatoria' else None,
            numero_vagas=5 if tipos_fase[i-1] == 'classificatoria' else None,
            status='não iniciada'
        )
    print('Fases criadas com sucesso')

    return selecao

def create_enrollments(alunos, selecao):
    for aluno in alunos:
        inscricao = Inscricao.objects.create(
            aluno=aluno.usuario,
            selecao=selecao,
            documento=None,
            observacao=fake.sentence()
        )
        print(f'Inscrição criada para {aluno.usuario.get_full_name()}')

def run_seed():
    print("Iniciando seed...")
    create_tipos_campo()
    alunos, professor = create_users()
    selecao = create_selection(professor)
    create_enrollments(alunos, selecao)
    if not Usuario.objects.filter(username='admin').exists():
        Usuario.objects.create(
            username='admin',
            first_name='Admin',
            last_name='Master',
            email='admin@example.com',
            is_superuser=True,
            is_staff=True,
            is_active=True,
            tipo_usuario='admin',
            cpf='00000000000',
            telefone='(00) 00000-0000',
            password=make_password('123456')
        )
        print('Usuário admin criado.')
    else:
        print('Usuário admin já existe.')
    print("Seed concluído com sucesso!")

if __name__ == '__main__':
    run_seed()