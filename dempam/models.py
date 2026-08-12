from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from localflavor.br.models import BRCNPJField
from django.core.validators import RegexValidator
from .utils import *


# Recursos Usados pelo Banco de Dados
class Complementos(): #Temporário
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)

# --- Informações sobre as Uas ---
class CircunscricaoPredio(models.Model):
    local = models.CharField(
        max_length=80,
        verbose_name='Local',
    )
    
    meso = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Mesorregião',
    )
    
    micro = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='Microrregião',
    )   
    
    class Meta:
        verbose_name = 'Circunscrição/Prédio'
        verbose_name_plural = '01 - Circunscrições/Prédios'

    def __str__(self):
        return self.local

class InfoUA(models.Model):
    circunscricao_predio = models.ForeignKey(
        CircunscricaoPredio,
        on_delete=models.PROTECT,
        related_name='circunscricoes_predios',
        verbose_name='Circunscricao/Prédio',
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='filhas',
        verbose_name='UA Pai',
    )

    codigo = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Código',
    )

    ua = models.CharField(
        max_length=100,
        verbose_name='UA',
    )

    sigla = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Sigla',
    )

    nivel = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Nível',
    )


    contato_ua = models.CharField(
        max_length=15,
        validators=[Complementos.validator_contato],
        blank=True,
        null=True,
        verbose_name='Contato da UA',
    )
    
    
    responsavel_ua = models.CharField(
        max_length=60, 
        default='Não Consta',
        blank=True,
        verbose_name='Responsável da UA',
    )
    
    
    mat_resp_ua = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Matrícula do Responsável da UA',
    )
    
    
    email_ua = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email da UA'
    )

    sede = models.BooleanField(
        default=False,
        blank=True,
        verbose_name='Sede',
    )

    gestor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uas_gerenciadas',
        verbose_name='Gestor da UA',
    )

    class Meta():
        verbose_name='UA'
        verbose_name_plural='02 - UAs'

    def __str__(self):
        if self.sigla:
            return f'{self.sigla} — {self.ua}'
        return self.ua


# --- Localização Interna no DEMPAM ---
class SetorDEMPAM(models.Model):
    setor = models.CharField(
        max_length=30,
        verbose_name='Setor/Sala'
    )
    
    class Meta():
        verbose_name='Setor/Sala DEMPAM'
        verbose_name_plural='03 - Setores/Salas DEMPAM'

    def __str__(self):
       return str(self.setor)

    @property
    def total_localizacoes(self):
        return self.localizacao_interna.count()

class LocalizacaoDEMPAM(models.Model):
    setor_sala = models.ForeignKey(
        SetorDEMPAM,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='localizacao_interna',
        verbose_name='Setor/Sala',
    )


    prateleira_pallet = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Prateleira/Pallet'
    )


    tipo_localizacao = models.CharField(
        max_length=30,
        choices=TipoLocalizacao.choices,
        blank=True,
        null=True,
    )

    corredor = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Corredor',
    )

    estante = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Estante',
    )

    prateleira = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Prateleira',
    )

    class Meta():
        verbose_name='Localização DEMPAM'
        verbose_name_plural='04 - Localizações DEMPAM'

    def save(self, *args, **kwargs):
        # quando é prateleira (não pallet), o código é composto de corredor + estante + prateleira
        # (ex.: corredor A, estante 3, prateleira 6 -> "A36") em vez de digitado à mão
        if self.tipo_localizacao == TipoLocalizacao.prateleira and self.corredor and self.estante and self.prateleira:
            self.prateleira_pallet = f'{self.corredor.strip().upper()}{self.estante.strip()}{self.prateleira.strip()}'
        super().save(*args, **kwargs)

    def __str__(self):
       return str(self.prateleira_pallet)


# --- Mural de Avisos do DEMPAM ---
class Aviso(models.Model):
    titulo = models.CharField(
        max_length=120,
        verbose_name='Título',
    )

    mensagem = models.TextField(
        verbose_name='Mensagem',
    )

    autor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='avisos_publicados',
        verbose_name='Autor',
    )

    data_publicacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Publicado em',
    )

    exibir_de = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Exibir a partir de',
        help_text='Deixe em branco para exibir imediatamente.',
    )

    exibir_ate = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Exibir até',
        help_text='Deixe em branco para não expirar automaticamente.',
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
    )

    class Meta:
        verbose_name = 'Aviso'
        verbose_name_plural = '05 - Avisos'
        ordering = ['-data_publicacao']

    def __str__(self):
        return self.titulo

    @property
    def esta_no_periodo(self):
        agora = timezone.now()
        if self.exibir_de and agora < self.exibir_de:
            return False
        if self.exibir_ate and agora > self.exibir_ate:
            return False
        return True


# --- Configuração do Painel de TV ---
class ConfiguracaoPainelTV(models.Model):
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Link do vídeo (YouTube ou link direto)',
    )

    video_arquivo = models.FileField(
        upload_to=path_video_painel_tv,
        blank=True,
        null=True,
        verbose_name='Arquivo de vídeo',
        help_text='Se enviado, tem prioridade sobre o link acima.',
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em',
    )

    atualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
        verbose_name='Atualizado por',
    )

    class Meta:
        verbose_name = 'Configuração do Painel de TV'
        verbose_name_plural = '06 - Configuração do Painel de TV'

    def __str__(self):
        return 'Configuração do Painel de TV'

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

