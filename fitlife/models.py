from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
 
# =============================================================================
# BLOCO 1 — ESTRUTURA BASE: Modalidade e Plano
# =============================================================================
 
class Modalidade(models.Model):
    """
    Modalidades de aulas coletivas oferecidas pela FitLife.
    Ex.: musculação, pilates, yoga, funcional.
    """
    DIFICULDADE_CHOICES = [
        ('Iniciante',     'Iniciante'),
        ('Intermediário', 'Intermediário'),
        ('Avançado',      'Avançado'),
    ]
 
    cod_modalidade = models.AutoField(primary_key=True, verbose_name='Código da Modalidade')
    nome_mod       = models.CharField(max_length=80, unique=True, verbose_name='Nome da Modalidade')
    descricao      = models.TextField(blank=True, null=True, verbose_name='Descrição')
    duracao        = models.PositiveSmallIntegerField(verbose_name='Duração (min)')
    dificuldade    = models.CharField(max_length=15, choices=DIFICULDADE_CHOICES, verbose_name='Dificuldade')
 
    class Meta:
        db_table            = 'modalidade'
        ordering            = ['nome_mod']
        verbose_name        = 'Modalidade'
        verbose_name_plural = 'Modalidades'
 
    def __str__(self):
        return f'{self.nome_mod} ({self.dificuldade})'
 
 
class Plano(models.Model):
    """
    Planos de assinatura da FitLife.
    Cada plano tem nome, descrição, valor e duração em dias.
    """
    cod_plano  = models.AutoField(primary_key=True, verbose_name='Código do Plano')
    nome_plano = models.CharField(max_length=100, verbose_name='Nome do Plano')
    descricao  = models.TextField(blank=True, null=True, verbose_name='Descrição')
    valor      = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor (R$)')
    duracao    = models.PositiveSmallIntegerField(verbose_name='Duração (dias)')
 
    class Meta:
        db_table            = 'plano'
        ordering            = ['nome_plano']
        verbose_name        = 'Plano'
        verbose_name_plural = 'Planos'
 
    def __str__(self):
        return f'{self.nome_plano} — R$ {self.valor} / {self.duracao} dias'
 
 
# =============================================================================
# BLOCO 2 — PROFESSOR (geral, CLT e PJ) e UNIDADE
# Professor é declarado antes de Unidade por causa da FK de gerente.
# =============================================================================
 
class Professor(models.Model):
    """
    Cadastro geral de professores, identificados pelo CREF.
    Inclui auto-relacionamento de supervisão (0,1)→(0,N).
    """
    cref            = models.CharField(max_length=20, primary_key=True, verbose_name='CREF')
    nome_prof       = models.CharField(max_length=150, verbose_name='Nome')
    cpf             = models.CharField(max_length=11, unique=True, verbose_name='CPF')
    e_mail          = models.EmailField(max_length=150, unique=True, verbose_name='E-mail')
    telefone        = models.CharField(max_length=20, verbose_name='Telefone')
    cref_supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='cref_supervisor',
        related_name='supervisionados',
        verbose_name='Supervisor'
    )
 
    class Meta:
        db_table            = 'professor'
        ordering            = ['nome_prof']
        verbose_name        = 'Professor'
        verbose_name_plural = 'Professores'
 
    def __str__(self):
        return f'{self.nome_prof} (CREF: {self.cref})'
 
    def tipo_vinculo(self):
        """Retorna 'CLT', 'PJ' ou 'Sem vínculo'."""
        if hasattr(self, 'clt'):
            return 'CLT'
        if hasattr(self, 'pj'):
            return 'PJ'
        return 'Sem vínculo'
 
 
class Unidade(models.Model):
    """
    Filiais (unidades) da rede FitLife.
    Cada unidade possui um gerente responsável (professor).
    """
    cod_unidade  = models.AutoField(primary_key=True, verbose_name='Código da Unidade')
    endereco     = models.CharField(max_length=255, verbose_name='Endereço')
    telefone     = models.CharField(max_length=20, verbose_name='Telefone')
    horario_func = models.CharField(
        max_length=100,
        verbose_name='Horário de Funcionamento',
        help_text='Ex.: Seg-Sex 06:00–22:00 / Sáb 08:00–14:00'
    )
    cref_gerente = models.ForeignKey(
        Professor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='cref_gerente',
        related_name='unidades_gerenciadas',
        verbose_name='Gerente Responsável'
    )
 
    class Meta:
        db_table            = 'unidade'
        ordering            = ['cod_unidade']
        verbose_name        = 'Unidade'
        verbose_name_plural = 'Unidades'
 
    def __str__(self):
        return f'Unidade {self.cod_unidade} — {self.endereco}'
 
 
# -----------------------------------------------------------------------------
# Subtipos de Professor: CLT e PJ
# Herança por tabela concreta (OneToOneField com primary_key=True).
# Regra de negócio: um professor NUNCA pode ter os dois vínculos ao mesmo tempo.
# -----------------------------------------------------------------------------
 
class CLT(models.Model):
    """
    Professor contratado no regime CLT.
    Atua em uma ÚNICA unidade da FitLife.
    Somente professores CLT podem conduzir avaliações físicas.
    """
    professor     = models.OneToOneField(
        Professor,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='cref',
        related_name='clt',
        verbose_name='Professor'
    )
    salario_fixo  = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salário Fixo (R$)')
    carga_horaria = models.PositiveSmallIntegerField(verbose_name='Carga Horária (h/semana)')
    data_admissao = models.DateField(verbose_name='Data de Admissão')
    cod_unidade   = models.ForeignKey(
        Unidade,
        on_delete=models.RESTRICT,
        db_column='cod_unidade',
        related_name='professores_clt',
        verbose_name='Unidade'
    )
 
    class Meta:
        db_table            = 'clt'
        verbose_name        = 'Professor CLT'
        verbose_name_plural = 'Professores CLT'
 
    def __str__(self):
        return f'{self.professor.nome_prof} — CLT | {self.cod_unidade}'
 
    def clean(self):
        """Impede duplo vínculo CLT + PJ."""
        if hasattr(self.professor, 'pj'):
            raise ValidationError(
                'Este professor já possui vínculo PJ. '
                'Um professor não pode ter CLT e PJ ao mesmo tempo.'
            )
 
 
class PJ(models.Model):
    """
    Professor autônomo (PJ).
    Pode atuar em múltiplas unidades via TrabalhaEmPJ.
    """
    professor                = models.OneToOneField(
        Professor,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='cref',
        related_name='pj',
        verbose_name='Professor'
    )
    cnpj                     = models.CharField(max_length=14, unique=True, verbose_name='CNPJ')
    valor_hora_aula          = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor por Hora/Aula (R$)')
    disponibilidade_horarios = models.TextField(blank=True, null=True, verbose_name='Disponibilidade de Horários')
 
    class Meta:
        db_table            = 'pj'
        verbose_name        = 'Professor PJ'
        verbose_name_plural = 'Professores PJ'
 
    def __str__(self):
        return f'{self.professor.nome_prof} — PJ (CNPJ: {self.cnpj})'
 
    def clean(self):
        """Impede duplo vínculo PJ + CLT."""
        if hasattr(self.professor, 'clt'):
            raise ValidationError(
                'Este professor já possui vínculo CLT. '
                'Um professor não pode ter PJ e CLT ao mesmo tempo.'
            )
 
 
class TrabalhaEmPJ(models.Model):
    """
    Relacionamento N:M entre professor PJ e as unidades onde atua.
    Chave composta: cref_pj + cod_unidade.
    """
    cref_pj     = models.ForeignKey(
        PJ,
        on_delete=models.CASCADE,
        db_column='cref_pj',
        related_name='unidades',
        verbose_name='Professor PJ'
    )
    cod_unidade = models.ForeignKey(
        Unidade,
        on_delete=models.CASCADE,
        db_column='cod_unidade',
        related_name='professores_pj',
        verbose_name='Unidade'
    )
 
    class Meta:
        db_table            = 'trabalha_em_pj'
        unique_together     = [('cref_pj', 'cod_unidade')]
        verbose_name        = 'Vínculo PJ × Unidade'
        verbose_name_plural = 'Vínculos PJ × Unidade'
 
    def __str__(self):
        return f'{self.cref_pj.professor.nome_prof} → {self.cod_unidade}'
 
 
# =============================================================================
# BLOCO 3 — ALUNO
# =============================================================================
 
class Aluno(models.Model):
    """
    Alunos matriculados na FitLife.
    Identificados pelo CPF. Podem ter restrições médicas registradas.
    """
    cpf             = models.CharField(max_length=11, primary_key=True, verbose_name='CPF')
    nome_aluno      = models.CharField(max_length=150, verbose_name='Nome Completo')
    data_nascimento = models.DateField(verbose_name='Data de Nascimento')
    endereco_aluno  = models.CharField(max_length=255, verbose_name='Endereço')
    telefone_aluno  = models.CharField(max_length=20, verbose_name='Telefone')
    e_mail          = models.EmailField(max_length=150, unique=True, verbose_name='E-mail')
    restricoes      = models.TextField(blank=True, null=True, verbose_name='Restrições Médicas')
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    class Meta:
        db_table            = 'aluno'
        ordering            = ['nome_aluno']
        verbose_name        = 'Aluno'
        verbose_name_plural = 'Alunos'
 
    def __str__(self):
        return f'{self.nome_aluno} (CPF: {self.cpf})'
 
    def contrato_ativo(self):
        """Retorna o contrato ativo do aluno, se houver."""
        return self.contratos.filter(status='Ativo').first()

 
# =============================================================================
# BLOCO 4 — CONTRATO, PAGAMENTO E FATURA
# =============================================================================
 
class ContratoPlan(models.Model):
    """
    Contratos de plano vinculando aluno, plano e unidade.
    Um aluno pode ter múltiplos contratos (histórico completo).
    """
    STATUS_CHOICES = [
        ('Ativo',     'Ativo'),
        ('Cancelado', 'Cancelado'),
        ('Expirado',  'Expirado'),
    ]
 
    num_contrato    = models.AutoField(primary_key=True, verbose_name='Número do Contrato')
    cpf_aluno       = models.ForeignKey(
        Aluno,
        on_delete=models.RESTRICT,
        db_column='cpf_aluno',
        to_field='cpf',
        related_name='contratos',
        verbose_name='Aluno'
    )
    cod_plano       = models.ForeignKey(
        Plano,
        on_delete=models.RESTRICT,
        db_column='cod_plano',
        related_name='contratos',
        verbose_name='Plano'
    )
    cod_unidade     = models.ForeignKey(
        Unidade,
        on_delete=models.RESTRICT,
        db_column='cod_unidade',
        related_name='contratos',
        verbose_name='Unidade'
    )
    data_inicio     = models.DateField(verbose_name='Data de Início')
    data_vencimento = models.DateField(verbose_name='Data de Vencimento')
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Ativo', verbose_name='Status')
 
    class Meta:
        db_table            = 'contrato_plano'
        ordering            = ['-data_inicio']
        verbose_name        = 'Contrato de Plano'
        verbose_name_plural = 'Contratos de Plano'
 
    def __str__(self):
        return f'Contrato #{self.num_contrato} — {self.cpf_aluno.nome_aluno} ({self.status})'
 
    def clean(self):
        """Data de vencimento deve ser posterior à data de início."""
        if self.data_vencimento and self.data_inicio:
            if self.data_vencimento <= self.data_inicio:
                raise ValidationError(
                    'A data de vencimento deve ser posterior à data de início.'
                )
 
 
class Pagamento(models.Model):
    """
    Cobranças geradas a partir de contratos de plano.
    Registra forma de pagamento, valor, vencimento e status.
    """
    FORMA_CHOICES = [
        ('PIX',               'PIX'),
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('Cartão de Débito',  'Cartão de Débito'),
        ('Boleto',            'Boleto'),
        ('Dinheiro',          'Dinheiro'),
    ]
    STATUS_CHOICES = [
        ('Pago',      'Pago'),
        ('Pendente',  'Pendente'),
        ('Atrasado',  'Atrasado'),
        ('Cancelado', 'Cancelado'),
    ]
 
    cod_pagamento   = models.AutoField(primary_key=True, verbose_name='Código do Pagamento')
    num_contrato    = models.ForeignKey(
        ContratoPlan,
        on_delete=models.RESTRICT,
        db_column='num_contrato',
        related_name='pagamentos',
        verbose_name='Contrato'
    )
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_CHOICES, verbose_name='Forma de Pagamento')
    valor           = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor (R$)')
    vencimento      = models.DateField(verbose_name='Vencimento')
    status_pag      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pendente', verbose_name='Status')
 
    class Meta:
        db_table            = 'pagamento'
        ordering            = ['vencimento']
        verbose_name        = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
 
    def __str__(self):
        return f'Pagamento #{self.cod_pagamento} — R$ {self.valor} ({self.status_pag})'
 
 
class Fatura(models.Model):
    """
    Faturas emitidas a partir de pagamentos.
    Tipos possíveis: NF-e, Recibo, NFSe.
    """
    cod_fatura    = models.AutoField(primary_key=True, verbose_name='Código da Fatura')
    cod_pagamento = models.ForeignKey(
        Pagamento,
        on_delete=models.RESTRICT,
        db_column='cod_pagamento',
        related_name='faturas',
        verbose_name='Pagamento'
    )
    tipo_fatura   = models.CharField(
        max_length=60,
        verbose_name='Tipo de Fatura',
        help_text='Ex.: NF-e, Recibo, NFSe'
    )
 
    class Meta:
        db_table            = 'fatura'
        verbose_name        = 'Fatura'
        verbose_name_plural = 'Faturas'
 
    def __str__(self):
        return f'Fatura #{self.cod_fatura} — {self.tipo_fatura}'
 
 
# =============================================================================
# BLOCO 5 — TURMA, INSCRIÇÃO E AVALIAÇÃO FÍSICA
# =============================================================================
 
class Turma(models.Model):
    """
    Turmas de aulas coletivas.
    Vincula modalidade, unidade, professor responsável e capacidade máxima.
    """
    cod_turma      = models.AutoField(primary_key=True, verbose_name='Código da Turma')
    cod_modalidade = models.ForeignKey(
        Modalidade,
        on_delete=models.RESTRICT,
        db_column='cod_modalidade',
        related_name='turmas',
        verbose_name='Modalidade'
    )
    cod_unidade    = models.ForeignKey(
        Unidade,
        on_delete=models.RESTRICT,
        db_column='cod_unidade',
        related_name='turmas',
        verbose_name='Unidade'
    )
    cref_professor = models.ForeignKey(
        Professor,
        on_delete=models.RESTRICT,
        db_column='cref_professor',
        related_name='turmas',
        verbose_name='Professor Responsável'
    )
    capacidade     = models.PositiveSmallIntegerField(verbose_name='Capacidade Máxima')
 
    class Meta:
        db_table            = 'turma'
        ordering            = ['cod_turma']
        verbose_name        = 'Turma'
        verbose_name_plural = 'Turmas'
 
    def __str__(self):
        return f'Turma #{self.cod_turma} — {self.cod_modalidade.nome_mod}'
 
    def vagas_disponiveis(self):
        """Retorna o número de vagas disponíveis na turma."""
        return self.capacidade - self.inscricoes.count()
 
    def esta_lotada(self):
        """Retorna True se a turma atingiu a capacidade máxima."""
        return self.inscricoes.count() >= self.capacidade
 
 
class Inscricao(models.Model):
    """
    Inscrições de alunos em turmas — relacionamento N:M.
    Chave composta: cpf_aluno + cod_turma.
    """
    cpf_aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        db_column='cpf_aluno',
        to_field='cpf',
        related_name='inscricoes',
        verbose_name='Aluno'
    )
    cod_turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        db_column='cod_turma',
        related_name='inscricoes',
        verbose_name='Turma'
    )
 
    class Meta:
        db_table            = 'inscricao'
        unique_together     = [('cpf_aluno', 'cod_turma')]
        verbose_name        = 'Inscrição'
        verbose_name_plural = 'Inscrições'
 
    def __str__(self):
        return f'{self.cpf_aluno.nome_aluno} → {self.cod_turma}'
 
    def clean(self):
        """Bloqueia inscrição quando a turma já está na capacidade máxima."""
        if self.cod_turma.esta_lotada():
            raise ValidationError(
                f'A turma "{self.cod_turma}" já atingiu a capacidade '
                f'máxima de {self.cod_turma.capacidade} alunos.'
            )
 
 
class AvaliacaoFisica(models.Model):
    """
    Avaliações físicas periódicas dos alunos.
    Regra: somente professores CLT podem conduzir avaliações.
    IMC é calculado como @property (equivalente ao GENERATED STORED do MySQL).
    """
    cod_avaliacao      = models.AutoField(primary_key=True, verbose_name='Código da Avaliação')
    cpf_aluno          = models.ForeignKey(
        Aluno,
        on_delete=models.RESTRICT,
        db_column='cpf_aluno',
        to_field='cpf',
        related_name='avaliacoes',
        verbose_name='Aluno'
    )
    # FK aponta para CLT — garante no próprio modelo que só professor CLT realiza avaliação
    cref_professor_clt = models.ForeignKey(
        CLT,
        on_delete=models.RESTRICT,
        db_column='cref_professor_clt',
        related_name='avaliacoes',
        verbose_name='Professor CLT'
    )
    data_avaliacao     = models.DateField(verbose_name='Data da Avaliação')
    peso               = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Peso (kg)')
    altura             = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Altura (m)')
    percentual_gordura = models.DecimalField(
        max_digits=5, decimal_places=2,
        blank=True, null=True,
        verbose_name='% de Gordura'
    )
    # JSON com circunferências: cintura, quadril, braço, coxa (em cm)
    circunferencias    = models.JSONField(
        blank=True, null=True,
        verbose_name='Circunferências (cm)',
        help_text='Ex.: {"cintura": 80, "quadril": 95, "braco": 35, "coxa": 58}'
    )
 
    class Meta:
        db_table            = 'avaliacao_fisica'
        ordering            = ['-data_avaliacao']
        verbose_name        = 'Avaliação Física'
        verbose_name_plural = 'Avaliações Físicas'
 
    def __str__(self):
        return (f'Avaliação #{self.cod_avaliacao} — '
                f'{self.cpf_aluno.nome_aluno} em {self.data_avaliacao}')
 
    @property
    def imc(self):
        """
        Calcula o IMC dinamicamente: peso / altura².
        Equivalente à coluna GENERATED STORED do MySQL.
        """
        if self.peso and self.altura and float(self.altura) > 0:
            return round(float(self.peso) / (float(self.altura) ** 2), 2)
        return None
 
    def classificacao_imc(self):
        """Classificação do IMC segundo a tabela da OMS."""
        valor = self.imc
        if valor is None:
            return 'Dados insuficientes'
        if valor < 18.5:
            return 'Abaixo do peso'
        if valor < 25.0:
            return 'Peso normal'
        if valor < 30.0:
            return 'Sobrepeso'
        return 'Obesidade'
