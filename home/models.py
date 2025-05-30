from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class Usuario(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
        ('admin', 'Administrador'),
    ]
    
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES)
    cpf = models.CharField(max_length=11, unique=True)
    telefone = models.CharField(max_length=15, blank=True)
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return self.get_full_name() or self.username

class Aluno(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_aluno',
        limit_choices_to={'tipo_usuario': 'aluno'}
    )
    curso = models.CharField(max_length=255)
    ira = models.DecimalField(max_digits=4, decimal_places=2)
    github = models.URLField(blank=True)
    interesse_pesquisa = models.CharField(max_length=255, blank=True)
    genero = models.CharField(max_length=50, blank=True)
    ppi = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'alunos'
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'
    
    def __str__(self):
        return self.usuario.get_full_name()

class Professor(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_professor',
        limit_choices_to={'tipo_usuario': 'professor'}
    )
    departamento = models.CharField(max_length=100)
    lattes = models.URLField(blank=True)
    area_atuacao = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'professores'
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'
    
    def __str__(self):
        return f"Prof. {self.usuario.get_full_name()}"

class Edital(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    arquivo = models.FileField(upload_to='editais/')
    data_publicacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='editais_criados'
    )
    ativo = models.BooleanField(default=True)
    nota_minima_aprovacao = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=7.0,
        help_text="Nota mínima para aprovação nas fases (0-10)"
    )
    
    class Meta:
        verbose_name = 'Edital'
        verbose_name_plural = 'Editais'
        ordering = ['-data_publicacao']
    
    def __str__(self):
        return self.titulo

class TipoCampo(models.Model):
    nome = models.CharField(max_length=50)
    tipo_dado = models.CharField(max_length=20, choices=[
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('data', 'Data'),
        ('arquivo', 'Arquivo'),
        ('escolha', 'Escolha Única'),
        ('multipla', 'Escolha Múltipla'),
        ('booleano', 'Verdadeiro/Falso'),
    ])
    opcoes = models.TextField(
        blank=True, 
        help_text="Para campos de escolha, informe uma opção por linha"
    )
    
    class Meta:
        verbose_name = 'Tipo de Campo'
        verbose_name_plural = 'Tipos de Campo'
    
    def __str__(self):
        return self.nome

class Selecao(models.Model):
    edital = models.ForeignKey(
        Edital, 
        on_delete=models.CASCADE, 
        related_name='selecoes'
    )
    professor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='selecoes_responsavel',
        limit_choices_to={'tipo_usuario': 'professor'},
    )
    data_inicio = models.DateTimeField(
        default=timezone.now,
        help_text="Use o formato YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]"
    )
    data_fim = models.DateTimeField(
        default=timezone.now,
        help_text="Use o formato YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]"
    )
    vagas = models.PositiveIntegerField(default=1)
    quantidade_fases = models.PositiveIntegerField(
        default=1,
        help_text="Número total de fases do processo seletivo"
    )
    fase_atual = models.PositiveIntegerField(
        default=1,
        help_text="Fase atual do processo seletivo"
    )
    def finalizar_fase_atual(self):
        """Finaliza a fase atual e avança para a próxima se todos foram avaliados"""
        try:
            fase_atual = self.fases_selecao.get(ordem=self.fase_atual)
        except Fase.DoesNotExist:
            return False

        inscricoes_na_fase = self.inscricoes.filter(fase_atual=self.fase_atual)
        
        # Verifica se todas as inscrições foram avaliadas
        todas_avaliadas = all(
            AvaliacaoFase.objects.filter(
                fase=fase_atual,
                inscricao=inscricao
            ).exists()
            for inscricao in inscricoes_na_fase
        )
        
        if todas_avaliadas:
            fase_atual.status = 'finalizada'
            fase_atual.save()
            
            if self.fase_atual < self.quantidade_fases:
                self.fase_atual += 1
                self.save()
                
                # Atualiza a próxima fase para "não iniciada"
                try:
                    proxima_fase = self.fases_selecao.get(ordem=self.fase_atual)
                    proxima_fase.status = 'não iniciada'
                    proxima_fase.save()
                except Fase.DoesNotExist:
                    pass
            else:
                # Todas as fases foram concluídas
                pass
            return True
        return False

    class Meta:
        verbose_name = 'Seleção'
        verbose_name_plural = 'Seleções'
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f"Seleção {self.edital.titulo}"
    
    def clean(self):
        if self.data_inicio >= self.data_fim:
            raise ValidationError("A data de término deve ser posterior à data de início")
        
        if self.data_inicio < timezone.now():
            raise ValidationError("A data de início não pode ser no passado")

class Fase(models.Model):
    TIPO_FASE_CHOICES = [
        ('classificatoria', 'Classificatória'),
        ('eliminatoria', 'Eliminatória'),
    ]
    
    selecao = models.ForeignKey(
        Selecao, 
        on_delete=models.CASCADE, 
        related_name='fases_selecao',
        null=True,
        blank=True
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=1)
    data_inicio = models.DateTimeField(
        default=timezone.now,
        help_text="Use o formato YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]"
    )
    data_fim = models.DateTimeField(
        default=timezone.now,
        help_text="Use o formato YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]"
    )
    tipo_fase = models.CharField(
        max_length=15,
        choices=TIPO_FASE_CHOICES,
        default='classificatoria'
    )
    peso = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.0,
        help_text="Peso desta fase na avaliação final (0-1)"
    )
    nota_corte = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=7.0,
        null=True,
        blank=True,
        help_text="Nota mínima para aprovação nesta fase (0-10)"
    )

    numero_vagas = models.PositiveIntegerField(
        default=1,
        null=True,
        blank=True,
        help_text="Número de inscrições que avançam para a próxima fase"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('não iniciada', 'Não iniciada'),
            ('atual', 'Atual'),
            ('finalizada', 'Finalizada'),
        ],
        default='não iniciada',
        help_text="Status atual da fase"
    )

    class Meta:
        verbose_name = 'Fase'
        verbose_name_plural = 'Fases'
        ordering = ['ordem']
        unique_together = ('selecao', 'ordem')
    
    def __str__(self):
        return f"{self.ordem}ª Fase - {self.nome}"
    
    def clean(self):
        if self.data_inicio >= self.data_fim:
            raise ValidationError("A data de término deve ser posterior à data de início")
        
        if self.selecao:
            if self.data_inicio < self.selecao.data_inicio or self.data_fim > self.selecao.data_fim:
                raise ValidationError("As datas da fase devem estar dentro do período da seleção")

class CampoFase(models.Model):
    fase = models.ForeignKey(
        Fase, 
        on_delete=models.CASCADE, 
        related_name='campos'
    )
    tipo = models.ForeignKey(
        TipoCampo, 
        on_delete=models.PROTECT,
        related_name='campos_fase'
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    obrigatorio = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(default=1)
    peso = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.0,
        help_text="Peso deste campo na avaliação da fase"
    )
    
    class Meta:
        verbose_name = 'Campo da Fase'
        verbose_name_plural = 'Campos da Fase'
        ordering = ['ordem']
        unique_together = ('fase', 'ordem')
    
    def __str__(self):
        return f"{self.nome} ({self.tipo.get_tipo_dado_display()})"

class Inscricao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('reprovada', 'Reprovada'),
    ]
    
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscricoes',
        limit_choices_to={'tipo_usuario': 'aluno'}
    )
    selecao = models.ForeignKey(
        Selecao, 
        on_delete=models.CASCADE, 
        related_name='inscricoes'
    )
    data_inscricao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente'
    )
    documento = models.FileField(upload_to='inscricoes/%Y/%m/')
    observacao = models.TextField(blank=True)
    nota_final = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    fase_atual = models.PositiveIntegerField(
        default=1,
        help_text="Fase atual do processo seletivo"
    )
    
    class Meta:
        verbose_name = 'Inscrição'
        verbose_name_plural = 'Inscrições'
        unique_together = ('aluno', 'selecao')
        ordering = ['-data_inscricao']
    
    def __str__(self):
        return f"Inscrição #{self.id}"
    
    def get_fase_atual(self):
        """Retorna o objeto da fase atual"""
        try:
            return self.selecao.fases_selecao.get(ordem=self.fase_atual)
        except Fase.DoesNotExist:
            return None
    
    def avancar_fase(self):
        """Avança para a próxima fase se aprovado na atual"""
        fase_atual = self.get_fase_atual()
        if not fase_atual:
            return False
            
        avaliacao = self.avaliacoes_fases.filter(fase=fase_atual).first()
        
        if avaliacao and avaliacao.aprovado:
            if self.fase_atual < self.selecao.quantidade_fases:
                self.fase_atual += 1
                self.save()
                return True
            else:
                self.status = 'aprovada'
                self.save()
                return False
        return False

    
    def reprovar(self):
        """Marca a inscrição como reprovada"""
        self.status = 'reprovada'
        self.save()
    
    def calcular_nota_final(self):
        """Calcula a nota final baseada nas avaliações das fases"""
        avaliacoes = self.avaliacoes_fases.filter(aprovado=True)
        if not avaliacoes.exists():
            return None
            
        total = 0
        peso_total = 0
        
        for avaliacao in avaliacoes:
            total += avaliacao.nota * avaliacao.fase.peso
            peso_total += avaliacao.fase.peso
        
        self.nota_final = (total / peso_total) if peso_total > 0 else 0
        self.save()
        return self.nota_final

class ValorCampoFase(models.Model):
    campo = models.ForeignKey(
        CampoFase, 
        on_delete=models.CASCADE, 
        related_name='valores'
    )
    inscricao = models.ForeignKey(
        Inscricao, 
        on_delete=models.CASCADE, 
        related_name='valores_campos'
    )
    valor_texto = models.TextField(blank=True, null=True)
    valor_numero = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    valor_data = models.DateField(blank=True, null=True)
    valor_arquivo = models.FileField(
        upload_to='fases/campos/', 
        blank=True, 
        null=True
    )
    valor_booleano = models.BooleanField(blank=True, null=True)
    avaliacao = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Nota atribuída pelo avaliador (0-10)"
    )
    observacao = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Valor de Campo'
        verbose_name_plural = 'Valores de Campos'
        unique_together = ('campo', 'inscricao')
    
    def __str__(self):
        return f"Valor para {self.campo.nome} (Inscrição {self.inscricao.id})"
    
    def get_valor(self):
        """Retorna o valor do campo de acordo com seu tipo"""
        tipo = self.campo.tipo.tipo_dado
        if tipo == 'texto':
            return self.valor_texto
        elif tipo == 'numero':
            return self.valor_numero
        elif tipo == 'data':
            return self.valor_data
        elif tipo == 'arquivo':
            return self.valor_arquivo
        elif tipo in ['escolha', 'multipla']:
            return self.valor_texto
        elif tipo == 'booleano':
            return self.valor_booleano
        return None

class AvaliacaoFase(models.Model):
    fase = models.ForeignKey(
        Fase, 
        on_delete=models.CASCADE, 
        related_name='avaliacoes'
    )
    inscricao = models.ForeignKey(
        Inscricao, 
        on_delete=models.CASCADE, 
        related_name='avaliacoes_fases'
    )
    avaliador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'tipo_usuario': 'professor'},
        related_name='avaliacoes_realizadas'
    )
    nota = models.DecimalField(max_digits=5, decimal_places=2)
    aprovado = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)
    data_avaliacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Avaliação de Fase'
        verbose_name_plural = 'Avaliações de Fases'
        unique_together = ('fase', 'inscricao', 'avaliador')
        ordering = ['-data_avaliacao']
    
    def __str__(self):
        return f"Avaliação de {self.inscricao.aluno} na fase {self.fase}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.inscricao.calcular_nota_final()
        
        avaliacoes_aprovadas = AvaliacaoFase.objects.filter(
            inscricao=self.inscricao,
            aprovado=True
        ).count()
        
        
        self.inscricao.save()