# Importações do Python
from decimal import Decimal

# Importações do Django
from django.db.models import Q
from django.utils import timezone

# Importações do código
from accounts.models import Profile, RegistroAcesso
from .models import Aviso
from dimrcbp.models import (
    AtribuicaoBem,
    Inventario,
    MovimentacaoBem,
    PeriodoInventario,
    SolicitacaoCatalogo,
    SolicitacaoTransferencia,
)
from dimrcbp.services import contar_bens_responsabilidade as _contar_bens_responsabilidade
from dimrcbp.utils import StatusSolicitacaoCatalogo, StatusSolicitacaoTransferencia
from dimms.models import Solicitacao
from dimms.models.solicitacoes import SolicitacaoItens, Tramitacao
from dimms.utils import StatusTramitacao

# ====================================
# SERVICES DO DEMPAM (PAINEL PRINCIPAL)
# ====================================


def obter_nome_usuario(user):
    return user.get_full_name() or user.username


def obter_perfil_label(user):
    if user.is_superuser:
        return 'Administrador do Sistema'
    if user.is_staff:
        return 'Equipe Técnica'
    if user.groups.filter(name='Gerencia').exists():
        return 'Gerência'
    if user.groups.exists():
        return ', '.join(g.name for g in user.groups.all())
    return 'Usuário Padrão'


def contar_bens_responsabilidade(user):
    return _contar_bens_responsabilidade(user)


def contar_acessos_mes(user):
    hoje = timezone.now()
    return RegistroAcesso.objects.filter(
        user=user, data__year=hoje.year, data__month=hoje.month
    ).count()


def _uas_do_usuario(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return list(profile.uas.all())


def _formatar_moeda(valor):
    texto = f'{valor:,.2f}'
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def obter_consumo_ua_ano(user):
    ano = timezone.now().year
    uas = _uas_do_usuario(user)
    if not uas:
        return {'pedidos': 0, 'valor': None}

    pedidos = Solicitacao.objects.filter(
        ua_order__in=uas,
        situation=StatusTramitacao.recebida,
        data_order__year=ano,
    )
    total_pedidos = pedidos.count()

    valor_total = Decimal('0')
    tem_preco = False
    itens = (
        SolicitacaoItens.objects
        .filter(request_defendant__in=pedidos)
        .select_related('item_order__item_shock')
    )
    for item in itens:
        if item.amount_order is None or not item.item_order or not item.item_order.item_shock:
            continue
        saldo = item.item_order.item_shock.saldos_ativos.order_by('-id').first()
        if saldo and saldo.preco_unitario is not None:
            valor_total += item.amount_order * saldo.preco_unitario
            tem_preco = True

    return {
        'pedidos': total_pedidos,
        'valor': _formatar_moeda(valor_total) if tem_preco else None,
    }


def contar_requisicoes_patrimonio_abertas(user):
    transferencia = SolicitacaoTransferencia.objects.filter(
        solicitante=user, status=StatusSolicitacaoTransferencia.pendente
    ).count()
    catalogo = SolicitacaoCatalogo.objects.filter(
        solicitante=user, status=StatusSolicitacaoCatalogo.pendente
    ).count()
    return {
        'total': transferencia + catalogo,
        'transferencia': transferencia,
        'catalogo': catalogo,
    }


def contar_requisicoes_consumo_abertas(user):
    uas = _uas_do_usuario(user)
    if not uas:
        return 0
    estados_abertos = [
        StatusTramitacao.atendimento,
        StatusTramitacao.aguar_separada,
        StatusTramitacao.separada,
        StatusTramitacao.em_expedicao,
    ]
    return Solicitacao.objects.filter(ua_order__in=uas, situation__in=estados_abertos).count()


def obter_alerta_inventario(user):
    periodo = PeriodoInventario.get_periodo_ativo()
    if not periodo:
        return None

    bens_ids = list(
        AtribuicaoBem.objects.filter(user=user, ativo=True).values_list('bem_id', flat=True)
    )
    total_bens = len(bens_ids)
    if not total_bens:
        return None

    ja_inventariados = Inventario.objects.filter(
        n_inventario=periodo, bem_id__in=bens_ids
    ).values_list('bem_id', flat=True).distinct().count()

    return {
        'periodo': periodo,
        'total_bens': total_bens,
        'pendentes': total_bens - ja_inventariados,
    }


def obter_ultimas_movimentacoes(user, limite=5):
    eventos = []

    for m in MovimentacaoBem.objects.filter(responsavel=user).select_related('bem', 'ua_destino')[:limite]:
        eventos.append({
            'data': m.data,
            'descricao': f'Bem {m.bem.tombo} movimentado para {m.ua_destino}',
            'tipo': 'patrimonio',
        })

    for t in Tramitacao.objects.filter(user_update=user).select_related('request_update').order_by('-date_update')[:limite]:
        if t.date_update is None:
            continue
        codigo = t.request_update.request_code if t.request_update else '?'
        eventos.append({
            'data': t.date_update,
            'descricao': f'Solicitação {codigo} → {t.get_update_display()}',
            'tipo': 'consumo',
        })

    eventos.sort(key=lambda e: e['data'], reverse=True)
    return eventos[:limite]


def obter_avisos(limite=5):
    agora = timezone.now()
    return (
        Aviso.objects
        .filter(ativo=True)
        .filter(Q(exibir_de__isnull=True) | Q(exibir_de__lte=agora))
        .filter(Q(exibir_ate__isnull=True) | Q(exibir_ate__gte=agora))
        .select_related('autor')[:limite]
    )


def montar_dashboard_usuario(user):
    return {
        'nome': obter_nome_usuario(user),
        'perfil_label': obter_perfil_label(user),
        'acessos_mes': contar_acessos_mes(user),
        'total_bens_responsabilidade': contar_bens_responsabilidade(user),
        'consumo_ua_ano': obter_consumo_ua_ano(user),
        'requisicoes_patrimonio_abertas': contar_requisicoes_patrimonio_abertas(user),
        'requisicoes_consumo_abertas': contar_requisicoes_consumo_abertas(user),
        'alerta_inventario': obter_alerta_inventario(user),
        'ultimas_movimentacoes': obter_ultimas_movimentacoes(user),
        'avisos': obter_avisos(),
    }
