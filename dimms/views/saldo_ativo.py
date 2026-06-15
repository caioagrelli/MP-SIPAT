# Importações do Django
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, Count
from django.views.decorators.http import require_POST
from django.urls import reverse

# Importações do código
from ..models import (
    SaldoAtivo, SolicitacoesSaldoAtivo, ItensSolicitados,
    BensEnviados, Contrato, Estoque
)
from ..utils import Status
from ..forms import SupplierForm

# ================================================
# VIEWS DO MÓDULO DE SALDO ATIVO
# ================================================


''' Homepage do Saldo Ativo '''
@login_required
def saldo_ativo_homepage(request):
    contratos = Contrato.objects.select_related('supplier_contract').annotate(
        total_itens=Count('Contrato', distinct=True),
        saldo_total=Sum('Contrato__saldo_disponivel'),
        solicitacoes_abertas=Count(
            'contrato_soli_saldoativo',
            filter=Q(contrato_soli_saldoativo__status__in=[Status.rascunho, Status.analise]),
            distinct=True
        )
    ).order_by('contrato')

    # KPIs
    total_contratos     = contratos.count()
    total_saldo         = SaldoAtivo.objects.aggregate(t=Sum('saldo_disponivel'))['t'] or 0
    solicitacoes_ativas = SolicitacoesSaldoAtivo.objects.filter(
        status__in=[Status.rascunho, Status.analise]
    ).count()

    solicitacoes_recentes = SolicitacoesSaldoAtivo.objects.select_related(
        'contrato', 'usuario'
    ).prefetch_related('bensenviados_saldoativo').order_by('-data_hora')[:10]

    context = {
        'contratos': contratos,
        'total_contratos': total_contratos,
        'total_saldo': total_saldo,
        'solicitacoes_ativas': solicitacoes_ativas,
        'solicitacoes_recentes': solicitacoes_recentes,
    }
    return render(request, 'dimms/saldo_ativo/homepage.html', context)


''' Cadastrar Fornecedor (acesso pelo Saldo Ativo) '''
@login_required
def fornecedor_criar_saldoativo(request):
    next_url = request.GET.get('next') or reverse('dimms:contrato_criar_saldoativo')

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Fornecedor "{supplier.supplier}" cadastrado com sucesso.')
            return redirect(request.POST.get('next') or reverse('dimms:contrato_criar_saldoativo'))
    else:
        form = SupplierForm()

    return render(request, 'dimms/saldo_ativo/fornecedor_create.html', {
        'form': form,
        'next_url': next_url,
    })


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
    ).select_related('bem__efisco', 'bem__contrato_saldo').prefetch_related('remessas')

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

    # Anotações de progresso por item
    from django.db.models import Sum as DSum
    itens_com_progresso = []
    for item in itens_solicitados:
        remessas = item.remessas.all()
        total_enviado  = sum(r.quantidade_enviada or 0 for r in remessas)
        total_recebido = sum(r.quantidade_enviada or 0 for r in remessas if r.recebida)
        pendentes      = [r for r in remessas if not r.recebida]
        pode_nova_remessa = total_enviado < (item.quantidade or 0)
        itens_com_progresso.append({
            'item': item,
            'remessas': remessas,
            'total_enviado': total_enviado,
            'total_recebido': total_recebido,
            'pendentes': pendentes,
            'pode_nova_remessa': pode_nova_remessa,
        })

    context = {
        'solicitacao': solicitacao,
        'itens_com_progresso': itens_com_progresso,
        'saldo_contrato': saldo_contrato,
        'status_choices': Status.choices,
        'pode_editar': solicitacao.status in [Status.rascunho, Status.analise],
    }
    return render(request, 'dimms/saldo_ativo/solicitacao_detail.html', context)


''' Registrar Remessa do Fornecedor (envio parcial ou total) '''
@login_required
def saldo_ativo_confirmar_envio(request, item_pk):
    item_solicitado = get_object_or_404(
        ItensSolicitados.objects.select_related('bem__efisco', 'solicitacao'),
        pk=item_pk
    )

    total_ja_enviado = item_solicitado.remessas.aggregate(
        t=Sum('quantidade_enviada')
    )['t'] or 0
    restante = (item_solicitado.quantidade or 0) - total_ja_enviado

    if restante <= 0:
        messages.warning(request, 'Todas as unidades deste item já foram registradas em remessas.')
        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=item_solicitado.solicitacao.pk)

    if request.method == 'POST':
        quantidade_enviada = request.POST.get('quantidade_enviada')
        observacao = request.POST.get('observacao', '').strip()

        if not quantidade_enviada:
            messages.error(request, 'Informe a quantidade enviada.')
        else:
            try:
                remessa = BensEnviados(
                    item_enviado=item_solicitado,
                    quantidade_enviada=int(quantidade_enviada),
                    observacao=observacao,
                )
                remessa.save()
                messages.success(request, f'Remessa de {quantidade_enviada} unidade(s) registrada. Aguardando recebimento.')
                return redirect('dimms:saldo_ativo_solicitacao_detail', pk=item_solicitado.solicitacao.pk)
            except Exception as e:
                messages.error(request, str(e))

    return render(request, 'dimms/saldo_ativo/confirmar_envio.html', {
        'item': item_solicitado,
        'restante': restante,
        'total_ja_enviado': total_ja_enviado,
    })


''' Confirmar Recebimento de uma Remessa → entra no estoque '''
@login_required
def saldo_ativo_confirmar_recebimento(request, remessa_pk):
    remessa = get_object_or_404(
        BensEnviados.objects.select_related(
            'item_enviado__bem__efisco',
            'item_enviado__bem__contrato_saldo',
            'item_enviado__solicitacao',
        ),
        pk=remessa_pk
    )

    if remessa.recebida:
        messages.warning(request, 'Esta remessa já foi recebida.')
        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=remessa.item_enviado.solicitacao.pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                remessa.recebida = True
                remessa.data_recebimento = timezone.now()
                # sem full_clean pois só estamos atualizando flags
                BensEnviados.objects.filter(pk=remessa.pk).update(
                    recebida=True,
                    data_recebimento=timezone.now(),
                )

                # Entra no estoque
                bem    = remessa.item_enviado.bem
                efisco = bem.efisco
                qtd    = remessa.quantidade_enviada or 0

                estoque_existente = Estoque.objects.filter(
                    item_shock=efisco,
                    mark=bem.marca or '',
                    form_input='Saldo Ativo',
                ).first()

                if estoque_existente:
                    estoque_existente.amount_shock += qtd
                    estoque_existente.save(update_fields=['amount_shock'])
                else:
                    Estoque.objects.create(
                        item_shock=efisco,
                        description_manual=bem.descricao_manual or efisco.descricao_efisco,
                        mark=bem.marca or '',
                        amount_shock=qtd,
                        form_input='Saldo Ativo',
                        method=f'Contrato {bem.contrato_saldo.contrato}',
                    )

            messages.success(request, f'{qtd} unidade(s) recebida(s) e registrada(s) no estoque.')
        except Exception as e:
            messages.error(request, str(e))

        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=remessa.item_enviado.solicitacao.pk)

    return render(request, 'dimms/saldo_ativo/confirmar_recebimento.html', {'remessa': remessa})


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
