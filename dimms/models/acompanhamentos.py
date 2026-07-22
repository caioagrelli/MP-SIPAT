# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.conf import settings
from django.db import models
from django.utils import timezone

# Importações do código
from ..utils import StatusAcompanhamentoSei

# =====================================
# MODELS DA DIMMS (ACOMPANHAMENTOS SEI)
# =====================================


''' Temas '''
# Tema — agrupa acompanhamentos de SEI por assunto, com uma cor pra identificação visual
class Subject(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Nome do Tema',
    )

    color = models.CharField(
        max_length=7,
        default='#2563EB',
        verbose_name='Cor',
        help_text='Cor em hexadecimal (ex.: #2563EB)',
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='temas_criados',
        verbose_name='Criado por',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tema'
        verbose_name_plural = '16 - Temas (Acompanhamentos)'
        ordering = ['name']


''' Acompanhamentos de SEI '''
# Um processo SEI sendo acompanhado, vinculado a um tema
class Sei(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='seis',
        verbose_name='Tema',
    )

    sei_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número do SEI',
        help_text='Ex.: 19.16.0001234567/2026-00',
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Assunto/Descrição',
    )

    status = models.CharField(
        max_length=20,
        choices=StatusAcompanhamentoSei.choices,
        default=StatusAcompanhamentoSei.em_andamento,
        verbose_name='Status',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seis_acompanhados',
        verbose_name='Responsável',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última modificação',
    )

    def __str__(self):
        return f'{self.sei_number} — {self.subject.name}'

    class Meta:
        verbose_name = 'Acompanhamento SEI'
        verbose_name_plural = '17 - Acompanhamentos SEI'
        ordering = ['-updated_at']


''' Atualizações '''
# Update/log de acompanhamento de um SEI — linha do tempo
class SeiUpdate(models.Model):
    sei = models.ForeignKey(
        Sei,
        on_delete=models.CASCADE,
        related_name='updates',
        verbose_name='Acompanhamento SEI',
    )

    text = models.TextField(
        verbose_name='Atualização',
    )

    date = models.DateField(
        default=timezone.localdate,
        verbose_name='Data da Atualização',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atualizacoes_sei',
        verbose_name='Registrado por',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    def __str__(self):
        return f'{self.sei.sei_number} — {self.date}'

    class Meta:
        verbose_name = 'Atualização SEI'
        verbose_name_plural = '18 - Atualizações SEI'
        ordering = ['-date', '-created_at']
