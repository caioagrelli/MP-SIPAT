# Importações do Django
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q

# Importações do código
from ..models import (
    SaldoAtivo, SolicitacoesSaldoAtivo, ItensSolicitados,
    BensEnviados, Contrato, Estoque
)
from ..utils import Status

# ================================================
# VIEWS DO MÓDULO DE SALDO ATIVO
# ================================================


''' Homepage do Saldo Ativo '''
@login_required
def saldo_ativo_homepage(request):
    query       = request.GET.get('q', '').strip()
    contrato_f  = request.GET.get('contrato', '').strip()
    cota_f      = request.GET.get('cota', '').strip()

    saldos = SaldoAtivo.objects.select_related(
        'contrato_saldo', 'efisco'
    ).order_by('contrato_saldo__contrato', 'efisco__descricao_efisco')

    if query:
        saldos = saldos.filter(
            Q(efisco__efisco__icontains=query) |
            Q(efisco__descricao_efisco__icontains=query) |
            Q(descricao_manual__icontains=query) |
            Q(marca__icontains=query)
        )

    if contrato_f:
        saldos = saldos.filter(contrato_saldo_id=contrato_f)

    if cota_f:
        saldos = saldos.filter(cota=cota_f)

    # KPIs
    total_itens         = saldos.count()
    saldo_total         = saldos.aggregate(t=Sum('saldo_disponivel'))['t'] or 0
    contratos_ativos    = Contrato.objects.filter(Contrato__isnull=False).distinct().count()
    solicitacoes_ativas = SolicitacoesSaldoAtivo.objects.filter(
        status__in=[Status.rascunho, Status.analise]
    ).count()

    # Solicitações recentes
    solicitacoes_recentes = SolicitacoesSaldoAtivo.objects.select_related(
        'contrato', 'usuario'
    ).order_by('-data_hora')[:10]

    # Contratos com saldo (para o filtro)
    contratos_com_saldo = Contrato.objects.filter(
        Contrato__isnull=False
    ).distinct()

    from ..utils import Cota
    cotas = Cota.choices

    context = {
        'saldos': saldos,
        'total_itens': total_itens,
        'saldo_total': saldo_total,
        'contratos_ativos': contratos_ativos,
        'solicitacoes_ativas': solicitacoes_ativas,
        'solicitacoes_recentes': solicitacoes_recentes,
        'contratos_com_saldo': contratos_com_saldo,
        'contrato_f': contrato_f,
        'cota_f': cota_f,
        'cotas': cotas,
        'query': query,
    }
    return render(request, 'dimms/saldo_ativo/homepage.html', context)


''' Criar Nova Solicitação de Saldo Ativo '''
@login_required
def saldo_ativo_solicitacao_create(request):
    contratos = Contrato.objects.filter(Contrato__isnull=False).distinct()

    if request.method == 'POST':
        contrato_id = request.POST.get('contrato')
        if not contrato_id:
            messages.error(request, 'Selecione um contrato.')
            return render(request, 'dimms/saldo_ativo/solicitacao_create.html', {
                'contratos': contratos
            })

        contrato = get_object_or_404(Contrato, pk=contrato_id)
        solicitacao = SolicitacoesSaldoAtivo.objects.create(
            contrato=contrato,
            usuario=request.user,
        )
        messages.success(request, f'Solicitação {solicitacao.codigo} criada com sucesso.')
        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=solicitacao.pk)

    return render(request, 'dimms/saldo_ativo/solicitacao_create.html', {
        'contratos': contratos
    })


''' Detalhes de uma Solicitação de Saldo Ativo '''
@login_required
def saldo_ativo_solicitacao_detail(request, pk):
    solicitacao = get_object_or_404(
        SolicitacoesSaldoAtivo.objects.select_related('contrato', 'usuario'),
        pk=pk
    )

    itens_solicitados = ItensSolicitados.objects.filter(
        solicitacao=solicitacao
    ).select_related('bem__efisco', 'bem__contrato_saldo')

    # Saldo disponível do contrato (para adicionar mais itens)
    saldo_contrato = SaldoAtivo.objects.filter(
        contrato_saldo=solicitacao.contrato
    ).select_related('efisco')

    # Adicionar item à solicitação
    if request.method == 'POST' and 'adicionar_item' in request.POST:
        bem_id    = request.POST.get('bem_id')
        quantidade = request.POST.get('quantidade')

        if not bem_id or not quantidade:
            messages.error(request, 'Preencha todos os campos.')
        else:
            bem = get_object_or_404(SaldoAtivo, pk=bem_id)
            try:
                quantidade = int(quantidade)
                item = ItensSolicitados(
                    solicitacao=solicitacao,
                    bem=bem,
                    quantidade=quantidade
                )
                item.full_clean()
                item.save()
                messages.success(request, 'Item adicionado à solicitação.')
            except Exception as e:
                messages.error(request, str(e))

        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=pk)

    # Remover item da solicitação
    if request.method == 'POST' and 'remover_item' in request.POST:
        item_id = request.POST.get('item_id')
        item = get_object_or_404(ItensSolicitados, pk=item_id, solicitacao=solicitacao)
        item.delete()
        messages.success(request, 'Item removido.')
        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=pk)

    # Alterar status
    if request.method == 'POST' and 'alterar_status' in request.POST:
        novo_status = request.POST.get('novo_status')
        if novo_status in dict(Status.choices):
            solicitacao.status = novo_status
            solicitacao.save()
            messages.success(request, f'Status alterado para {solicitacao.get_status_display()}.')
        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=pk)

    context = {
        'solicitacao': solicitacao,
        'itens_solicitados': itens_solicitados,
        'saldo_contrato': saldo_contrato,
        'status_choices': Status.choices,
        'pode_editar': solicitacao.status in [Status.rascunho, Status.analise],
    }
    return render(request, 'dimms/saldo_ativo/solicitacao_detail.html', context)


''' Confirmar Envio de Itens e Entrada no Estoque '''
@login_required
def saldo_ativo_confirmar_envio(request, item_pk):
    item_solicitado = get_object_or_404(
        ItensSolicitados.objects.select_related(
            'bem__efisco', 'solicitacao'
        ),
        pk=item_pk
    )

    # Verificar se já foi enviado
    if hasattr(item_solicitado, 'itemenviado'):
        messages.warning(request, 'Este item já foi enviado.')
        return redirect('dimms:saldo_ativo_solicitacao_detail',
                        pk=item_solicitado.solicitacao.pk)

    if request.method == 'POST':
        quantidade_enviada = request.POST.get('quantidade_enviada')

        if not quantidade_enviada:
            messages.error(request, 'Informe a quantidade enviada.')
            return render(request, 'dimms/saldo_ativo/confirmar_envio.html', {
                'item': item_solicitado
            })

        try:
            quantidade_enviada = int(quantidade_enviada)

            with transaction.atomic():
                # 1. Criar registro de envio (isso decrementa o saldo_disponivel automaticamente)
                envio = BensEnviados(
                    item_enviado=item_solicitado,
                    quantidade_enviada=quantidade_enviada,
                )
                envio.full_clean()
                envio.save()

                # 2. Criar ou incrementar entrada no Estoque
                bem = item_solicitado.bem
                efisco = bem.efisco

                estoque_existente = Estoque.objects.filter(
                    item_shock=efisco,
                    mark=bem.marca or '',
                    form_input='Saldo Ativo',
                ).first()

                if estoque_existente:
                    estoque_existente.amount_shock += quantidade_enviada
                    estoque_existente.save(update_fields=['amount_shock'])
                else:
                    Estoque.objects.create(
                        item_shock=efisco,
                        description_manual=bem.descricao_manual or efisco.descricao_efisco,
                        mark=bem.marca or '',
                        amount_shock=quantidade_enviada,
                        form_input='Saldo Ativo',
                        method=f'Contrato {bem.contrato_saldo.contrato}',
                    )

            messages.success(
                request,
                f'{quantidade_enviada} unidade(s) enviada(s) e registrada(s) no estoque.'
            )
            return redirect('dimms:saldo_ativo_solicitacao_detail',
                            pk=item_solicitado.solicitacao.pk)

        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'dimms/saldo_ativo/confirmar_envio.html', {
        'item': item_solicitado
    })


''' Lista de Solicitações '''
@login_required
def saldo_ativo_solicitacoes(request):
    status_f    = request.GET.get('status', '').strip()
    contrato_f  = request.GET.get('contrato', '').strip()
    query       = request.GET.get('q', '').strip()

    solicitacoes = SolicitacoesSaldoAtivo.objects.select_related(
        'contrato', 'usuario'
    ).order_by('-data_hora')

    if status_f:
        solicitacoes = solicitacoes.filter(status=status_f)

    if contrato_f:
        solicitacoes = solicitacoes.filter(contrato_id=contrato_f)

    if query:
        solicitacoes = solicitacoes.filter(
            Q(codigo__icontains=query) |
            Q(contrato__contrato__icontains=query)
        )

    contratos = Contrato.objects.filter(
        contrato_soli_saldoativo__isnull=False
    ).distinct()

    context = {
        'solicitacoes': solicitacoes,
        'status_choices': Status.choices,
        'contratos': contratos,
        'status_f': status_f,
        'contrato_f': contrato_f,
        'query': query,
        'total': solicitacoes.count(),
    }
    return render(request, 'dimms/saldo_ativo/solicitacoes.html', context)
