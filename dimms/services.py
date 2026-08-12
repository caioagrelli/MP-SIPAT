# Importações do Django
import logging
from urllib.parse import quote

import requests
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

# Importações do código
from .models import Estoque, SolicitacaoItens

# ====================================
# SERVICES DA DIMMS (BENS DE CONSUMO)
# ====================================

logger = logging.getLogger(__name__)



# função para calcular o consumo mensal de um bem
def recalcular_consumo():
    hoje = timezone.now()

    for estoque in Estoque.objects.all():
        if not estoque.created_at:
            estoque.monthly_consumption = 0
            estoque.save(update_fields=["monthly_consumption"])
            continue

        dias_desde_cadastro = max((hoje.date() - estoque.created_at.date()).days, 1)

        total_saida = (
            SolicitacaoItens.objects
            .filter(
                item_order=estoque,
                request_defendant__stock_deducted=True,
            )
            .aggregate(total=Sum("amount_order"))
            .get("total") or 0
        )

        consumo_mensal = (
            Decimal(total_saida) / Decimal(dias_desde_cadastro) * Decimal("30")
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        estoque.monthly_consumption = int(consumo_mensal)
        estoque.save(update_fields=["monthly_consumption"])


# ====================================
# WHATSAPP (EVOLUTION API)
# ====================================


def _normalizar_numero_whatsapp(numero):
    ''' Deixa só dígitos e garante o DDI 55 (Brasil), como a Evolution API espera. '''
    if not numero:
        return None

    digitos = ''.join(c for c in numero if c.isdigit())
    if not digitos:
        return None

    if not digitos.startswith('55'):
        digitos = '55' + digitos

    return digitos


def enviar_whatsapp(numero, mensagem):
    '''
    Envia uma mensagem de texto via Evolution API.
    Nunca levanta exceção pro chamador — se der errado, só loga e retorna False,
    pra uma falha de WhatsApp nunca quebrar o fluxo principal (ex: separar uma solicitação).
    '''
    numero_normalizado = _normalizar_numero_whatsapp(numero)
    if not numero_normalizado:
        return False

    if not (settings.EVOLUTION_API_URL and settings.EVOLUTION_API_KEY and settings.EVOLUTION_INSTANCE):
        logger.warning('Evolution API não configurada (EVOLUTION_API_URL/API_KEY/INSTANCE) — mensagem não enviada.')
        return False

    url = f'{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE}'
    headers = {'apikey': settings.EVOLUTION_API_KEY}
    payload = {'number': numero_normalizado, 'text': mensagem}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception('Falha ao enviar WhatsApp via Evolution API para %s', numero_normalizado)
        return False


def notificar_ua_solicitacao_separada(solicitacao):
    ''' Avisa a UA, por WhatsApp, que a solicitação dela foi separada e já está pronta pra retirada. '''
    ua = solicitacao.ua_order
    if not ua or not ua.contato_ua:
        return False

    linhas = [
        '📦 *SIPAT — Solicitação Separada*',
        '',
        f'Solicitação: {solicitacao.request_code}',
    ]

    if solicitacao.numero_pe_integrado:
        linhas.append(f'N° PE Integrado: {solicitacao.numero_pe_integrado}')

    linhas.append(f'UA: {ua}')

    if solicitacao.user_order:
        linhas.append(f'Solicitante: {solicitacao.user_order}')

    contato_duvidas = _normalizar_numero_whatsapp('81992320369')

    texto_duvida = f'Olá, tenho uma dúvida sobre a solicitação {solicitacao.request_code}'
    if solicitacao.numero_pe_integrado:
        texto_duvida += f' (N° PE Integrado: {solicitacao.numero_pe_integrado})'
    texto_duvida += f', da UA {ua}.'
    link_duvidas = f'https://wa.me/{contato_duvidas}?text={quote(texto_duvida)}'

    linhas += [
        '',
        'Sua solicitação de bens de consumo já foi separada e está pronta para retirada.',
        '',
        f'Em caso de dúvidas, fale com o almoxarifado: {link_duvidas}',
    ]

    mensagem = '\n'.join(linhas)
    return enviar_whatsapp(ua.contato_ua, mensagem)
