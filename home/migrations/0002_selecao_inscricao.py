# Generated by Django 5.1.7 on 2025-03-26 15:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Selecao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_inicio', models.DateTimeField()),
                ('data_fim', models.DateTimeField()),
                ('edital', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='selecao', to='home.edital')),
                ('professor_responsavel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='selecoes_como_professor', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Inscricao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_inscricao', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('aprovada', 'Aprovada'), ('reprovada', 'Reprovada')], default='pendente', max_length=20)),
                ('documento', models.FileField(upload_to='inscricoes/')),
                ('aluno', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inscricoes_como_aluno', to=settings.AUTH_USER_MODEL)),
                ('selecao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.selecao')),
            ],
            options={
                'unique_together': {('aluno', 'selecao')},
            },
        ),
    ]
