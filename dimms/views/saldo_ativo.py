# Importações do Django
import os
from io import BytesIO

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, Count
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.staticfiles import finders

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

# Importações do código
from ..models import (
    SaldoAtivo, SolicitacoesSaldoAtivo, ItensSolicitados,
    BensEnviados, Contrato, Estoque, Supplier
)
from ..utils import Status, StatusContrato, parse_quantidade
from ..forms import SupplierForm

# ================================================
# VIEWS DO MÓDULO DE SALDO ATIVO
# ================================================


''' Homepage do Saldo Ativo '''
@login_required
def saldo_ativo_homepage(request):
    q = request.GET.get('q', '').strip()

    contratos = Contrato.objects.select_related('supplier_contract').annotate(
        total_itens=Count('Contrato', distinct=True),
        saldo_total=Sum('Contrato__saldo_disponivel'),
        solicitacoes_abertas=Count(
            'contrato_soli_saldoativo',
            filter=Q(contrato_soli_saldoativo__status__in=[Status.rascunho, Status.analise]),
            distinct=True
        )
    ).order_by('contrato')

    if q:
        contratos = contratos.filter(
            Q(contrato__icontains=q) |
            Q(supplier_contract__supplier__icontains=q)
        )

    # KPIs (sobre todos os contratos, sem filtro de busca)
    total_contratos     = Contrato.objects.count()
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
        'q': q,
        'contratos_encontrados': contratos.count(),
    }
    return render(request, 'dimms/saldo_ativo/homepage.html', context)


''' Lista de Fornecedores '''
@login_required
def fornecedor_lista(request):
    q = request.GET.get('q', '').strip()
    fornecedores = Supplier.objects.annotate(
        total_contratos=Count('contrato', distinct=True),
        total_saldo=Sum('contrato__Contrato__saldo_disponivel'),
    ).order_by('supplier')
    if q:
        fornecedores = fornecedores.filter(
            Q(supplier__icontains=q) | Q(cnpj_supplier__icontains=q)
        )
    return render(request, 'dimms/saldo_ativo/fornecedor_lista.html', {
        'fornecedores': fornecedores,
        'q': q,
        'total': fornecedores.count(),
    })


''' Detalhe e edição de Fornecedor '''
@login_required
def fornecedor_detail(request, pk):
    from ..forms import SupplierForm
    fornecedor = get_object_or_404(Supplier, pk=pk)

    contratos = Contrato.objects.filter(supplier_contract=fornecedor).annotate(
        total_itens=Count('Contrato', distinct=True),
        saldo_total=Sum('Contrato__saldo_disponivel'),
    ).order_by('contrato')

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor atualizado com sucesso.')
            return redirect('dimms:fornecedor_detail', pk=pk)
    else:
        form = SupplierForm(instance=fornecedor)

    return render(request, 'dimms/saldo_ativo/fornecedor_detail.html', {
        'fornecedor': fornecedor,
        'form': form,
        'contratos': contratos,
    })


''' Busca de Fornecedores (autocomplete JSON) '''
@login_required
def fornecedor_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse([], safe=False)
    resultados = (
        Supplier.objects
        .filter(supplier__icontains=q)
        .values('id', 'supplier', 'cnpj_supplier')
        [:15]
    )
    return JsonResponse(list(resultados), safe=False)


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
def saldo_ativo_contrato_search(request):
    """Busca contratos por número ou fornecedor para autocomplete."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    from ..models import Contrato
    qs = (
        Contrato.objects
        .filter(Contrato__isnull=False)
        .exclude(status=StatusContrato.cancelado)
        .filter(
            Q(contrato__icontains=q) |
            Q(numero_contrato_oficial__icontains=q) |
            Q(supplier_contract__supplier__icontains=q)
        )
        .select_related('supplier_contract')
        .distinct()[:20]
    )
    results = [
        {
            'id': c.pk,
            'numero': c.contrato,
            'fornecedor': str(c.supplier_contract) if c.supplier_contract else '',
            'numero_oficial': c.numero_contrato_oficial or '',
        }
        for c in qs
    ]
    return JsonResponse({'results': results})


@login_required
def saldo_ativo_itens_por_contrato(request):
    """Retorna itens disponíveis de um contrato como JSON (para o formulário dinâmico)."""
    contrato_id = request.GET.get('contrato_id')
    if not contrato_id:
        return JsonResponse({'itens': []})
    itens = (
        SaldoAtivo.objects
        .filter(contrato_saldo_id=contrato_id, saldo_disponivel__gt=0)
        .exclude(contrato_saldo__status=StatusContrato.cancelado)
        .select_related('efisco')
        .order_by('efisco__descricao_efisco')
    )
    data = [
        {
            'id': i.pk,
            'efisco': i.efisco.efisco,
            'descricao': i.descricao_manual or i.efisco.descricao_efisco or '',
            'marca': i.marca or '',
            'saldo': i.saldo_disponivel or 0,
            'preco': float(i.preco_unitario) if i.preco_unitario else None,
            'unidade': i.efisco.get_medida_display() if hasattr(i.efisco, 'get_medida_display') else '',
        }
        for i in itens
    ]
    return JsonResponse({'itens': data})


@login_required
def saldo_ativo_solicitacao_create(request):
    contratos = (
        Contrato.objects
        .filter(Contrato__isnull=False)
        .exclude(status=StatusContrato.cancelado)
        .distinct()
        .select_related('supplier_contract')
    )
    contrato_pre = request.GET.get('contrato', '')

    if request.method == 'POST':
        contrato_id = request.POST.get('contrato')
        numero_nota_fiscal = request.POST.get('numero_nota_fiscal', '').strip()
        numero_sei = request.POST.get('numero_sei', '').strip()
        numero_empenho = request.POST.get('numero_empenho', '').strip()
        nota_fiscal_file = request.FILES.get('nota_fiscal')
        empenho_file = request.FILES.get('empenho')
        termo_recebimento_file = request.FILES.get('termo_recebimento_definitivo')

        if not contrato_id:
            messages.error(request, 'Selecione um contrato.')
            return render(request, 'dimms/saldo_ativo/solicitacao_create.html', {
                'contratos': contratos, 'contrato_pre': contrato_pre,
            })

        contrato = get_object_or_404(Contrato, pk=contrato_id)

        # Coleta itens selecionados
        itens_selecionados = []
        for key, valor in request.POST.items():
            if not key.startswith('qtd_'):
                continue
            try:
                saldo_pk = int(key[4:])
                quantidade = parse_quantidade(valor)
            except (ValueError, TypeError):
                continue
            if quantidade > 0:
                itens_selecionados.append((saldo_pk, quantidade))

        if not itens_selecionados:
            messages.error(request, 'Adicione pelo menos um item à solicitação.')
            return render(request, 'dimms/saldo_ativo/solicitacao_create.html', {
                'contratos': contratos, 'contrato_pre': contrato_pre,
            })

        try:
            with transaction.atomic():
                solicitacao = SolicitacoesSaldoAtivo(
                    contrato=contrato,
                    usuario=request.user,
                    numero_nota_fiscal=numero_nota_fiscal,
                    numero_sei=numero_sei,
                    numero_empenho=numero_empenho,
                )
                if nota_fiscal_file:
                    solicitacao.nota_fiscal = nota_fiscal_file
                if empenho_file:
                    solicitacao.empenho = empenho_file
                if termo_recebimento_file:
                    solicitacao.termo_recebimento_definitivo = termo_recebimento_file
                solicitacao.save()

                erros = []
                adicionados = 0
                for saldo_pk, quantidade in itens_selecionados:
                    bem = get_object_or_404(SaldoAtivo, pk=saldo_pk)
                    try:
                        item = ItensSolicitados(solicitacao=solicitacao, bem=bem, quantidade=quantidade)
                        item.full_clean()
                        item.save()
                        adicionados += 1
                    except Exception as e:
                        erros.append(f'{bem.efisco.efisco}: {e}')

                if erros:
                    for erro in erros:
                        messages.warning(request, erro)
        except Exception as e:
            messages.error(request, f'Erro ao criar solicitação: {e}')
            return render(request, 'dimms/saldo_ativo/solicitacao_create.html', {
                'contratos': contratos, 'contrato_pre': contrato_pre,
            })

        messages.success(request, f'Solicitação {solicitacao.codigo} criada com {adicionados} item(ns).')
        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=solicitacao.pk)

    contrato_pre_obj = None
    if contrato_pre:
        try:
            contrato_pre_obj = Contrato.objects.select_related('supplier_contract').get(pk=contrato_pre)
        except (Contrato.DoesNotExist, ValueError):
            pass

    return render(request, 'dimms/saldo_ativo/solicitacao_create.html', {
        'contrato_pre': contrato_pre,
        'contrato_pre_obj': contrato_pre_obj,
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
    # Contrato cancelado não permite adicionar novos itens.
    if solicitacao.contrato.status == StatusContrato.cancelado:
        saldo_contrato = SaldoAtivo.objects.none()
    else:
        saldo_contrato = SaldoAtivo.objects.filter(
            contrato_saldo=solicitacao.contrato
        ).select_related('efisco')

    # Adicionar múltiplos itens de uma vez
    if request.method == 'POST' and 'adicionar_itens' in request.POST:
        from django.core.exceptions import ValidationError as DjangoValidationError
        adicionados = 0
        erros = []
        for key, valor in request.POST.items():
            if not key.startswith('qtd_'):
                continue
            try:
                saldo_pk = int(key[4:])
                quantidade = parse_quantidade(valor)
            except (ValueError, TypeError):
                continue
            if quantidade <= 0:
                continue
            bem = get_object_or_404(SaldoAtivo, pk=saldo_pk)

            # Impede duplicata com mensagem legível
            if ItensSolicitados.objects.filter(solicitacao=solicitacao, bem=bem).exists():
                erros.append(f'{bem.efisco.efisco}: item já está na solicitação.')
                continue

            try:
                item = ItensSolicitados(
                    solicitacao=solicitacao,
                    bem=bem,
                    quantidade=quantidade,
                )
                # save() já chama full_clean() e desconta o saldo
                item.save()
                adicionados += 1
            except DjangoValidationError as e:
                msgs = '; '.join(m for m in e.messages)
                erros.append(f'{bem.efisco.efisco}: {msgs}')
            except Exception as e:
                erros.append(f'{bem.efisco.efisco}: {e}')

        if adicionados:
            messages.success(request, f'{adicionados} item(ns) adicionado(s) e saldo reservado.')
        for erro in erros:
            messages.error(request, erro)
        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=pk)

    # Excluir solicitação
    if request.method == 'POST' and 'excluir_solicitacao' in request.POST:
        solicitacao.delete()
        messages.success(request, 'Solicitação excluída.')
        return redirect('dimms:saldo_ativo_solicitacoes')

    # Remover item da solicitação
    if request.method == 'POST' and 'remover_item' in request.POST:
        item_id = request.POST.get('item_id')
        item = get_object_or_404(ItensSolicitados, pk=item_id, solicitacao=solicitacao)
        item.delete()
        messages.success(request, 'Item removido.')
        return redirect('dimms:saldo_ativo_solicitacao_detail', pk=pk)

    # Atualizar dados da solicitação (SEI, empenho, nota fiscal, termo de recebimento)
    if request.method == 'POST' and 'atualizar_dados' in request.POST:
        solicitacao.numero_sei = request.POST.get('numero_sei', '').strip()
        solicitacao.numero_empenho = request.POST.get('numero_empenho', '').strip()
        solicitacao.numero_nota_fiscal = request.POST.get('numero_nota_fiscal', '').strip()

        if 'nota_fiscal' in request.FILES:
            solicitacao.nota_fiscal = request.FILES['nota_fiscal']
        elif request.POST.get('remover_nota_fiscal'):
            solicitacao.nota_fiscal = None

        if 'empenho' in request.FILES:
            solicitacao.empenho = request.FILES['empenho']
        elif request.POST.get('remover_empenho'):
            solicitacao.empenho = None

        if 'termo_recebimento_definitivo' in request.FILES:
            solicitacao.termo_recebimento_definitivo = request.FILES['termo_recebimento_definitivo']
        elif request.POST.get('remover_termo_recebimento_definitivo'):
            solicitacao.termo_recebimento_definitivo = None

        solicitacao.save(update_fields=[
            'numero_sei', 'numero_empenho', 'numero_nota_fiscal',
            'nota_fiscal', 'empenho', 'termo_recebimento_definitivo',
        ])
        messages.success(request, 'Dados da solicitação atualizados.')
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
        restante = (item.quantidade or 0) - total_enviado
        pode_nova_remessa = restante > 0
        itens_com_progresso.append({
            'item': item,
            'remessas': remessas,
            'total_enviado': total_enviado,
            'total_recebido': total_recebido,
            'pendentes': pendentes,
            'pode_nova_remessa': pode_nova_remessa,
            'restante': restante,
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
        comprovante = request.FILES.get('comprovante')

        if not quantidade_enviada:
            messages.error(request, 'Informe a quantidade registrada.')
        else:
            try:
                qtd = parse_quantidade(quantidade_enviada)
                with transaction.atomic():
                    remessa = BensEnviados(
                        item_enviado=item_solicitado,
                        quantidade_enviada=qtd,
                        observacao=observacao,
                        recebida=True,
                        data_recebimento=timezone.now(),
                    )
                    if comprovante:
                        remessa.comprovante = comprovante
                    remessa.save()

                    # Adiciona ao estoque ao confirmar o recebimento
                    bem    = item_solicitado.bem
                    efisco = bem.efisco
                    existente = Estoque.objects.filter(item_shock=efisco).first()
                    if existente:
                        existente.amount_shock += qtd
                        existente.save(update_fields=['amount_shock'])
                    else:
                        Estoque.objects.create(
                            item_shock=efisco,
                            description_manual=bem.descricao_manual or efisco.descricao_efisco,
                            mark=bem.marca or '',
                            amount_shock=qtd,
                            form_input='Saldo Ativo',
                            method=f'Contrato {bem.contrato_saldo.contrato}',
                        )

                messages.success(request, f'{qtd} unidade(s) registradas e adicionadas ao estoque.')
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

                estoque_existente = Estoque.objects.filter(item_shock=efisco).first()

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
    status_f   = request.GET.get('status', '').strip()
    contrato_f = request.GET.get('contrato', '').strip()
    query      = request.GET.get('q', '').strip()

    base = SolicitacoesSaldoAtivo.objects.select_related(
        'contrato__supplier_contract', 'usuario'
    ).annotate(
        num_itens=Count('bensenviados_saldoativo', distinct=True),
    ).order_by('-data_hora')

    solicitacoes = base
    if status_f:
        solicitacoes = solicitacoes.filter(status=status_f)
    if contrato_f:
        solicitacoes = solicitacoes.filter(contrato_id=contrato_f)
    if query:
        solicitacoes = solicitacoes.filter(
            Q(codigo__icontains=query) |
            Q(contrato__contrato__icontains=query) |
            Q(contrato__supplier_contract__supplier__icontains=query)
        )

    contratos = Contrato.objects.filter(
        contrato_soli_saldoativo__isnull=False
    ).distinct().order_by('contrato')

    all_qs = SolicitacoesSaldoAtivo.objects
    context = {
        'solicitacoes':   solicitacoes,
        'status_choices': Status.choices,
        'contratos':      contratos,
        'status_f':       status_f,
        'contrato_f':     contrato_f,
        'query':          query,
        'total':          solicitacoes.count(),
        'kpi_total':      all_qs.count(),
        'kpi_abertas':    all_qs.filter(status__in=[Status.rascunho, Status.analise]).count(),
        'kpi_atendidas':  all_qs.filter(status=Status.atendida).count(),
        'kpi_canceladas': all_qs.filter(status=Status.cancelada).count(),
    }
    return render(request, 'dimms/saldo_ativo/solicitacoes.html', context)


# ────────────────────────────────────────────────────────────────
# HELPERS PDF
# ────────────────────────────────────────────────────────────────

def _pdf_header(c, w, h_page, titulo, subtitulo='', codigo='', data_str=''):
    logo_path = finders.find('img/brasao-mppe.png')
    logo_reader = ImageReader(logo_path) if logo_path and os.path.exists(logo_path) else None

    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(0, h_page - 42*mm, w, 42*mm, fill=1, stroke=0)

    if logo_reader:
        c.drawImage(logo_reader, 12*mm, h_page - 35*mm, width=20*mm, height=20*mm, mask='auto')

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(36*mm, h_page - 16*mm, 'MINISTÉRIO PÚBLICO DE PERNAMBUCO')
    c.setFont('Helvetica', 8.5)
    c.drawString(36*mm, h_page - 23*mm, 'SIPAT — Sistema Integrado Patrimonial de Apoio Técnico')
    c.setFont('Helvetica-Bold', 10)
    c.drawString(36*mm, h_page - 31*mm, titulo.upper())
    if subtitulo:
        c.setFont('Helvetica', 8)
        c.drawString(36*mm, h_page - 37*mm, subtitulo)

    c.setFont('Helvetica', 8)
    if codigo:
        c.drawRightString(w - 12*mm, h_page - 16*mm, codigo)
    if data_str:
        c.drawRightString(w - 12*mm, h_page - 23*mm, data_str)

    return h_page - 52*mm


def _pdf_section(c, w, title, y):
    c.setFillColor(colors.HexColor('#2563eb'))
    c.rect(12*mm, y - 7*mm, w - 24*mm, 7.5*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(15*mm, y - 4.8*mm, title.upper())
    return y - 14*mm


def _pdf_row(c, w, label, value, y, shade=False):
    rh = 7*mm
    if shade:
        c.setFillColor(colors.HexColor('#f7f8fc'))
        c.rect(12*mm, y - rh, w - 24*mm, rh, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica-Bold', 7)
    c.drawString(15*mm, y - 4.8*mm, label.upper())
    c.setFillColor(colors.HexColor('#1a2035'))
    c.setFont('Helvetica', 8.5)
    c.drawString(72*mm, y - 4.8*mm, str(value) if value else '—')
    c.setStrokeColor(colors.HexColor('#e2e5ef'))
    c.setLineWidth(0.3)
    c.line(12*mm, y - rh, w - 12*mm, y - rh)
    return y - rh


def _check_page(c, y, w, h_page, margin=25):
    if y < margin*mm:
        c.showPage()
        c.setFillColor(colors.HexColor('#1e2d42'))
        c.rect(0, h_page - 8*mm, w, 8*mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica', 7)
        c.drawString(12*mm, h_page - 5.5*mm, 'SIPAT — Continuação')
        return h_page - 16*mm
    return y


def _fmt_dt(dt):
    if not dt:
        return '—'
    from django.utils import timezone as tz
    local = tz.localtime(dt)
    return local.strftime('%d/%m/%Y às %H:%M')


# ────────────────────────────────────────────────────────────────
# PDF: RELATÓRIO DA SOLICITAÇÃO
# ────────────────────────────────────────────────────────────────

@login_required
def pdf_relatorio_solicitacao(request, pk):
    solicitacao = get_object_or_404(
        SolicitacoesSaldoAtivo.objects.select_related('contrato__supplier_contract', 'usuario'),
        pk=pk
    )
    itens = list(
        ItensSolicitados.objects
        .filter(solicitacao=solicitacao)
        .select_related('bem__efisco', 'bem__contrato_saldo')
        .prefetch_related('remessas')
    )

    # Pré-calcula totais por item
    dados = []
    for item in itens:
        remessas = list(item.remessas.all().order_by('data_envio'))
        total_enviado  = sum(r.quantidade_enviada or 0 for r in remessas)
        total_recebido = sum(r.quantidade_enviada or 0 for r in remessas if r.recebida)
        pendente = (item.quantidade or 0) - total_recebido
        dados.append({
            'item': item,
            'remessas': remessas,
            'total_enviado': total_enviado,
            'total_recebido': total_recebido,
            'pendente': max(pendente, 0),
        })

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="solicitacao_{solicitacao.codigo}.pdf"'

    w, h_page = A4
    c = rl_canvas.Canvas(resp, pagesize=A4)

    gerado_em = _fmt_dt(timezone.now())
    responsavel = ''
    if solicitacao.usuario:
        responsavel = solicitacao.usuario.get_full_name() or solicitacao.usuario.username

    # ── PÁGINA 1: cabeçalho + dados + tabela resumo ──────────────────────────
    y = _pdf_header(
        c, w, h_page,
        titulo='Relatório de Solicitação — Saldo Ativo',
        subtitulo=(
            f'Contrato: {solicitacao.contrato.contrato}  |  '
            f'Fornecedor: {solicitacao.contrato.supplier_contract or "—"}'
        ),
        codigo=solicitacao.codigo,
        data_str=f'Gerado em {gerado_em}',
    )

    # Bloco de dados da solicitação (2 colunas lado a lado)
    y = _pdf_section(c, w, 'Dados da Solicitação', y)
    nota_fiscal_ref = '—'
    if solicitacao.nota_fiscal:
        import os as _os
        nota_fiscal_ref = _os.path.basename(solicitacao.nota_fiscal.name)

    meta = [
        ('Código',        solicitacao.codigo),
        ('Status',        solicitacao.get_status_display()),
        ('Contrato',      solicitacao.contrato.contrato),
        ('Data Abertura', _fmt_dt(solicitacao.data_hora)),
        ('Fornecedor',    str(solicitacao.contrato.supplier_contract or '—')),
        ('Responsável',   responsavel or '—'),
        ('N° SEI',        solicitacao.numero_sei or '—'),
        ('N° Empenho',    solicitacao.numero_empenho or '—'),
        ('Nota Fiscal',   nota_fiscal_ref),
    ]
    col_w = (w - 24*mm) / 2
    for i in range(0, len(meta), 2):
        rh = 7*mm
        shade = (i // 2) % 2 == 1
        if shade:
            c.setFillColor(colors.HexColor('#f7f8fc'))
            c.rect(12*mm, y - rh, w - 24*mm, rh, fill=1, stroke=0)
        for j, (lbl, val) in enumerate(meta[i:i+2]):
            x = 12*mm + j * col_w
            c.setFillColor(colors.HexColor('#7380a0'))
            c.setFont('Helvetica-Bold', 7)
            c.drawString(x + 3*mm, y - 4.8*mm, lbl.upper())
            c.setFillColor(colors.HexColor('#1a2035'))
            c.setFont('Helvetica', 8.5)
            c.drawString(x + 38*mm, y - 4.8*mm, str(val)[:38])
        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.3)
        c.line(12*mm, y - rh, w - 12*mm, y - rh)
        y -= rh

    y -= 8*mm

    # ── TABELA RESUMO DE ITENS ──────────────────────────────────────────────
    y = _pdf_section(c, w, 'Resumo dos Itens Solicitados', y)

    # Colunas: E-Fisco | Descrição | Marca | Unidade | Solicitado | Recebido | Pendente | Status
    CX = [12, 30, 80, 125, 143, 157, 171, 185]  # mm
    CW = [18, 50, 45, 18,  14,  14,  14,  w/mm - 185 - 12]
    HDR = ['E-FISCO', 'DESCRIÇÃO', 'MARCA / UNID.', 'SOLIC.', 'RECEB.', 'PEND.', 'STATUS']

    # Cabeçalho da tabela
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(12*mm, y - 7*mm, w - 24*mm, 7.5*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 6.5)
    for i, (txt, x) in enumerate(zip(HDR, CX)):
        c.drawString(x*mm + 1.5*mm, y - 4.8*mm, txt)
    y -= 8*mm

    for idx, d in enumerate(dados):
        y = _check_page(c, y, w, h_page)
        item = d['item']
        rh = 8*mm
        shade = idx % 2 == 1
        if shade:
            c.setFillColor(colors.HexColor('#f7f8fc'))
            c.rect(12*mm, y - rh, w - 24*mm, rh, fill=1, stroke=0)

        desc  = (item.bem.descricao_manual or item.bem.efisco.descricao_efisco or '')[:40]
        marca = (item.bem.marca or '—')[:18]
        unid  = (item.bem.efisco.get_medida_display() if item.bem.efisco.medida else '—')[:12]

        recebido = d['total_recebido']
        pendente = d['pendente']
        solicitado = item.quantidade or 0
        completo = recebido >= solicitado

        c.setFillColor(colors.HexColor('#1d4ed8'))
        c.setFont('Helvetica-Bold', 7.5)
        c.drawString(CX[0]*mm + 1.5*mm, y - 5*mm, str(item.bem.efisco.efisco))

        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica', 7.5)
        c.drawString(CX[1]*mm + 1.5*mm, y - 5*mm, desc)

        c.setFont('Helvetica', 7)
        c.setFillColor(colors.HexColor('#3d4966'))
        c.drawString(CX[2]*mm + 1.5*mm, y - 4*mm, marca)
        c.setFillColor(colors.HexColor('#7380a0'))
        c.drawString(CX[2]*mm + 1.5*mm, y - 7.2*mm, unid)

        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(CX[3]*mm + 7*mm, y - 5*mm, str(solicitado))

        c.setFillColor(colors.HexColor('#15803d'))
        c.drawCentredString(CX[4]*mm + 7*mm, y - 5*mm, str(recebido))

        c.setFillColor(colors.HexColor('#b45309') if pendente > 0 else colors.HexColor('#15803d'))
        c.drawCentredString(CX[5]*mm + 7*mm, y - 5*mm, str(pendente))

        # Status pill
        status_txt  = 'Completo' if completo else ('Parcial' if recebido > 0 else 'Pendente')
        status_color = '#15803d' if completo else ('#1d4ed8' if recebido > 0 else '#b45309')
        pill_x = CX[6]*mm + 1.5*mm
        pill_w = (w/mm - 12 - CX[6]) * mm
        c.setFillColor(colors.HexColor(status_color))
        c.roundRect(pill_x, y - 6.5*mm, pill_w - 2*mm, 5.5*mm, 2*mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 6)
        c.drawCentredString(pill_x + (pill_w - 2*mm)/2, y - 4.2*mm, status_txt)

        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.2)
        c.line(12*mm, y - rh, w - 12*mm, y - rh)
        y -= rh

    # Linha de totais
    y -= 2*mm
    total_sol = sum(d['item'].quantidade or 0 for d in dados)
    total_rec = sum(d['total_recebido'] for d in dados)
    total_pen = sum(d['pendente'] for d in dados)
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(12*mm, y - 7*mm, w - 24*mm, 7.5*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(15*mm, y - 4.8*mm, f'TOTAL — {len(dados)} item(ns)')
    c.drawCentredString(CX[3]*mm + 7*mm, y - 4.8*mm, str(total_sol))
    c.setFillColor(colors.HexColor('#bbf7d0'))
    c.drawCentredString(CX[4]*mm + 7*mm, y - 4.8*mm, str(total_rec))
    c.setFillColor(colors.HexColor('#fde68a') if total_pen > 0 else colors.HexColor('#bbf7d0'))
    c.drawCentredString(CX[5]*mm + 7*mm, y - 4.8*mm, str(total_pen))
    y -= 10*mm

    # ── DETALHAMENTO DAS REMESSAS ─────────────────────────────────────────────
    has_remessas = any(d['remessas'] for d in dados)
    if has_remessas:
        y = _check_page(c, y, w, h_page, margin=40)
        y = _pdf_section(c, w, 'Detalhamento das Remessas por Item', y)

        RC = [12, 22, 72, 122, 145, 162, 180]  # mm
        RH = ['Nº', 'DATA REMESSA', 'DATA RECEBIMENTO', 'QTDE', 'REC.', 'OBS.']

        for d in dados:
            if not d['remessas']:
                continue
            item = d['item']
            y = _check_page(c, y, w, h_page, margin=35)

            # Sub-header do item
            desc = (item.bem.descricao_manual or item.bem.efisco.descricao_efisco or '')[:60]
            c.setFillColor(colors.HexColor('#eff4ff'))
            c.rect(12*mm, y - 8*mm, w - 24*mm, 8.5*mm, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor('#c7d7fd'))
            c.setLineWidth(0.5)
            c.rect(12*mm, y - 8*mm, w - 24*mm, 8.5*mm, fill=0, stroke=1)
            c.setFillColor(colors.HexColor('#1d4ed8'))
            c.setFont('Helvetica-Bold', 8.5)
            c.drawString(15*mm, y - 5.2*mm, str(item.bem.efisco.efisco))
            c.setFillColor(colors.HexColor('#3d4966'))
            c.setFont('Helvetica', 8)
            c.drawString(36*mm, y - 5.2*mm, desc)
            y -= 10*mm

            # Cabeçalho colunas
            c.setFillColor(colors.HexColor('#374151'))
            c.rect(12*mm, y - 6*mm, w - 24*mm, 6.5*mm, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont('Helvetica-Bold', 6.5)
            for txt, x in zip(RH, RC):
                c.drawString(x*mm + 1*mm, y - 4.2*mm, txt)
            y -= 7*mm

            for idx, r in enumerate(d['remessas']):
                y = _check_page(c, y, w, h_page)
                rh = 7.5*mm
                if idx % 2 == 0:
                    c.setFillColor(colors.HexColor('#f7f8fc'))
                    c.rect(12*mm, y - rh, w - 24*mm, rh, fill=1, stroke=0)

                c.setFillColor(colors.HexColor('#7380a0'))
                c.setFont('Helvetica', 7.5)
                c.drawString(RC[0]*mm + 1*mm, y - 4.8*mm, str(idx + 1))

                c.setFillColor(colors.HexColor('#1a2035'))
                c.drawString(RC[1]*mm + 1*mm, y - 4.8*mm, _fmt_dt(r.data_envio))

                if r.data_recebimento:
                    c.setFillColor(colors.HexColor('#15803d'))
                    c.drawString(RC[2]*mm + 1*mm, y - 4.8*mm, _fmt_dt(r.data_recebimento))
                else:
                    c.setFillColor(colors.HexColor('#b45309'))
                    c.drawString(RC[2]*mm + 1*mm, y - 4.8*mm, 'Aguardando recebimento')

                c.setFillColor(colors.HexColor('#1a2035'))
                c.setFont('Helvetica-Bold', 8)
                c.drawCentredString(RC[3]*mm + 9*mm, y - 4.8*mm, str(r.quantidade_enviada or 0))

                rec_txt = 'Sim' if r.recebida else 'Não'
                c.setFillColor(colors.HexColor('#15803d') if r.recebida else colors.HexColor('#b45309'))
                c.setFont('Helvetica-Bold', 7.5)
                c.drawCentredString(RC[4]*mm + 8*mm, y - 4.8*mm, rec_txt)

                if r.observacao:
                    c.setFillColor(colors.HexColor('#7380a0'))
                    c.setFont('Helvetica-Oblique', 6.5)
                    c.drawString(RC[5]*mm + 1*mm, y - 4.8*mm, r.observacao[:35])

                c.setStrokeColor(colors.HexColor('#e2e5ef'))
                c.setLineWidth(0.2)
                c.line(12*mm, y - rh, w - 12*mm, y - rh)
                y -= rh

            y -= 6*mm

    # ── Rodapé todas as páginas ────────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7)
    c.drawCentredString(w / 2, 10*mm, f'SIPAT — {solicitacao.codigo} — Gerado em {gerado_em}')

    c.save()
    return resp


# ────────────────────────────────────────────────────────────────
# PDF: CARGA RECEBIDA (TERMO DE RECEBIMENTO)
# ────────────────────────────────────────────────────────────────

@login_required
def pdf_carga_recebida(request, pk):
    import os as _os
    solicitacao = get_object_or_404(
        SolicitacoesSaldoAtivo.objects.select_related('contrato__supplier_contract', 'usuario'),
        pk=pk
    )
    itens = list(
        ItensSolicitados.objects
        .filter(solicitacao=solicitacao)
        .select_related('bem__efisco', 'bem__contrato_saldo')
        .prefetch_related('remessas')
    )

    # Apenas itens com pelo menos uma remessa recebida
    dados = []
    for item in itens:
        remessas_recebidas = [r for r in item.remessas.all().order_by('data_recebimento') if r.recebida]
        total_recebido = sum(r.quantidade_enviada or 0 for r in remessas_recebidas)
        if total_recebido > 0:
            dados.append({
                'item': item,
                'remessas': remessas_recebidas,
                'total_recebido': total_recebido,
            })

    resp = HttpResponse(content_type='application/pdf')
    safe_code = (solicitacao.codigo or 'carga').replace('/', '-')
    resp['Content-Disposition'] = f'inline; filename="carga_recebida_{safe_code}.pdf"'

    w, h_page = A4
    c = rl_canvas.Canvas(resp, pagesize=A4)

    gerado_em = _fmt_dt(timezone.now())
    responsavel = ''
    if solicitacao.usuario:
        responsavel = solicitacao.usuario.get_full_name() or solicitacao.usuario.username

    nota_fiscal_ref = '—'
    if solicitacao.nota_fiscal:
        nota_fiscal_ref = _os.path.basename(solicitacao.nota_fiscal.name)

    # ── CABEÇALHO ───────────────────────────────────────────────
    y = _pdf_header(
        c, w, h_page,
        titulo='Termo de Recebimento de Carga — Saldo Ativo',
        subtitulo=(
            f'Contrato: {solicitacao.contrato.contrato}  |  '
            f'Fornecedor: {solicitacao.contrato.supplier_contract or "—"}'
        ),
        codigo=solicitacao.codigo,
        data_str=f'Gerado em {gerado_em}',
    )

    # ── DADOS DA SOLICITAÇÃO ─────────────────────────────────────
    y = _pdf_section(c, w, 'Dados da Solicitação', y)
    meta = [
        ('Código',        solicitacao.codigo),
        ('Data Abertura', _fmt_dt(solicitacao.data_hora)),
        ('Contrato',      solicitacao.contrato.contrato),
        ('Fornecedor',    str(solicitacao.contrato.supplier_contract or '—')),
        ('Responsável',   responsavel or '—'),
        ('Status',        solicitacao.get_status_display()),
        ('N° SEI',        solicitacao.numero_sei or '—'),
        ('N° Empenho',    solicitacao.numero_empenho or '—'),
        ('Nota Fiscal',   nota_fiscal_ref),
    ]
    col_w = (w - 24*mm) / 2
    for i in range(0, len(meta), 2):
        rh = 7*mm
        shade = (i // 2) % 2 == 1
        if shade:
            c.setFillColor(colors.HexColor('#f7f8fc'))
            c.rect(12*mm, y - rh, w - 24*mm, rh, fill=1, stroke=0)
        for j, (lbl, val) in enumerate(meta[i:i+2]):
            x = 12*mm + j * col_w
            c.setFillColor(colors.HexColor('#7380a0'))
            c.setFont('Helvetica-Bold', 7)
            c.drawString(x + 3*mm, y - 4.8*mm, lbl.upper())
            c.setFillColor(colors.HexColor('#1a2035'))
            c.setFont('Helvetica', 8.5)
            c.drawString(x + 38*mm, y - 4.8*mm, str(val)[:38])
        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.3)
        c.line(12*mm, y - rh, w - 12*mm, y - rh)
        y -= rh

    y -= 8*mm

    # ── TABELA DE ITENS RECEBIDOS ────────────────────────────────
    y = _pdf_section(c, w, 'Itens Recebidos', y)

    # Colunas: E-Fisco | Descrição | Marca | Unid. | Solicitado | Recebido
    CX2 = [12, 32, 90, 138, 155, 168, 182]  # mm
    HDR2 = ['E-FISCO', 'DESCRIÇÃO', 'MARCA', 'UNID.', 'SOLIC.', 'RECEBIDO']

    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(12*mm, y - 7*mm, w - 24*mm, 7.5*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 6.5)
    for txt, x in zip(HDR2, CX2):
        c.drawString(x*mm + 1.5*mm, y - 4.8*mm, txt)
    y -= 8*mm

    total_sol_geral = 0
    total_rec_geral = 0

    for idx, d in enumerate(dados):
        y = _check_page(c, y, w, h_page)
        item = d['item']
        rh = 8*mm
        shade = idx % 2 == 1
        if shade:
            c.setFillColor(colors.HexColor('#f7f8fc'))
            c.rect(12*mm, y - rh, w - 24*mm, rh, fill=1, stroke=0)

        desc  = (item.bem.descricao_manual or item.bem.efisco.descricao_efisco or '')[:50]
        marca = (item.bem.marca or '—')[:18]
        unid  = (item.bem.efisco.get_medida_display() if item.bem.efisco.medida else '—')[:10]
        sol   = item.quantidade or 0
        rec   = d['total_recebido']

        total_sol_geral += sol
        total_rec_geral += rec

        completo = rec >= sol

        c.setFillColor(colors.HexColor('#1d4ed8'))
        c.setFont('Helvetica-Bold', 7.5)
        c.drawString(CX2[0]*mm + 1.5*mm, y - 5*mm, str(item.bem.efisco.efisco))

        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica', 7.5)
        c.drawString(CX2[1]*mm + 1.5*mm, y - 5*mm, desc)

        c.setFillColor(colors.HexColor('#3d4966'))
        c.setFont('Helvetica', 7)
        c.drawString(CX2[2]*mm + 1.5*mm, y - 5*mm, marca)
        c.drawString(CX2[3]*mm + 1.5*mm, y - 5*mm, unid)

        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(CX2[4]*mm + 7*mm, y - 5*mm, str(sol))

        c.setFillColor(colors.HexColor('#15803d') if completo else colors.HexColor('#b45309'))
        c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(CX2[5]*mm + 7*mm, y - 5*mm, str(rec))

        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.2)
        c.line(12*mm, y - rh, w - 12*mm, y - rh)
        y -= rh

    # Linha de totais
    y -= 2*mm
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(12*mm, y - 7*mm, w - 24*mm, 7.5*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(15*mm, y - 4.8*mm, f'TOTAL — {len(dados)} item(ns) recebido(s)')
    c.drawCentredString(CX2[4]*mm + 7*mm, y - 4.8*mm, str(total_sol_geral))
    c.setFillColor(colors.HexColor('#bbf7d0'))
    c.drawCentredString(CX2[5]*mm + 7*mm, y - 4.8*mm, str(total_rec_geral))
    y -= 12*mm

    # ── DETALHAMENTO DAS REMESSAS RECEBIDAS ──────────────────────
    if any(d['remessas'] for d in dados):
        y = _check_page(c, y, w, h_page, margin=50)
        y = _pdf_section(c, w, 'Detalhamento das Remessas Recebidas', y)

        for d in dados:
            if not d['remessas']:
                continue
            item = d['item']
            y = _check_page(c, y, w, h_page, margin=40)

            desc = (item.bem.descricao_manual or item.bem.efisco.descricao_efisco or '')[:65]
            c.setFillColor(colors.HexColor('#eff4ff'))
            c.rect(12*mm, y - 8*mm, w - 24*mm, 8.5*mm, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor('#c7d7fd'))
            c.setLineWidth(0.5)
            c.rect(12*mm, y - 8*mm, w - 24*mm, 8.5*mm, fill=0, stroke=1)
            c.setFillColor(colors.HexColor('#1d4ed8'))
            c.setFont('Helvetica-Bold', 8.5)
            c.drawString(15*mm, y - 5.2*mm, str(item.bem.efisco.efisco))
            c.setFillColor(colors.HexColor('#3d4966'))
            c.setFont('Helvetica', 8)
            c.drawString(38*mm, y - 5.2*mm, desc)
            y -= 10*mm

            RC = [12, 22, 62, 120, 148, 165]  # mm
            RH = ['Nº', 'DATA RECEBIMENTO', 'OBS.', 'QTDE RECEBIDA', 'COMPROVANTE']
            c.setFillColor(colors.HexColor('#374151'))
            c.rect(12*mm, y - 6*mm, w - 24*mm, 6.5*mm, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont('Helvetica-Bold', 6.5)
            for txt, x in zip(RH, RC):
                c.drawString(x*mm + 1*mm, y - 4.2*mm, txt)
            y -= 7*mm

            for idx2, r in enumerate(d['remessas']):
                y = _check_page(c, y, w, h_page)
                rh = 7.5*mm
                if idx2 % 2 == 0:
                    c.setFillColor(colors.HexColor('#f7f8fc'))
                    c.rect(12*mm, y - rh, w - 24*mm, rh, fill=1, stroke=0)

                c.setFillColor(colors.HexColor('#7380a0'))
                c.setFont('Helvetica', 7.5)
                c.drawString(RC[0]*mm + 1*mm, y - 4.8*mm, str(idx2 + 1))

                c.setFillColor(colors.HexColor('#15803d'))
                c.setFont('Helvetica', 7.5)
                c.drawString(RC[1]*mm + 1*mm, y - 4.8*mm, _fmt_dt(r.data_recebimento))

                if r.observacao:
                    c.setFillColor(colors.HexColor('#7380a0'))
                    c.setFont('Helvetica-Oblique', 6.5)
                    c.drawString(RC[2]*mm + 1*mm, y - 4.8*mm, r.observacao[:40])

                c.setFillColor(colors.HexColor('#15803d'))
                c.setFont('Helvetica-Bold', 9)
                c.drawCentredString(RC[3]*mm + 12*mm, y - 4.8*mm, str(r.quantidade_enviada or 0))

                if r.comprovante:
                    comp_name = _os.path.basename(r.comprovante.name)[:30]
                    c.setFillColor(colors.HexColor('#1d4ed8'))
                    c.setFont('Helvetica', 6.5)
                    c.drawString(RC[4]*mm + 1*mm, y - 4.8*mm, comp_name)
                else:
                    c.setFillColor(colors.HexColor('#7380a0'))
                    c.setFont('Helvetica', 7)
                    c.drawString(RC[4]*mm + 1*mm, y - 4.8*mm, '—')

                c.setStrokeColor(colors.HexColor('#e2e5ef'))
                c.setLineWidth(0.2)
                c.line(12*mm, y - rh, w - 12*mm, y - rh)
                y -= rh

            y -= 6*mm

    # ── BLOCO DE ASSINATURAS ─────────────────────────────────────
    y = _check_page(c, y, w, h_page, margin=55)
    y -= 14*mm
    sig_w = (w - 40*mm) / 2
    sig_y = y - 12*mm

    c.setStrokeColor(colors.HexColor('#c8cfe0'))
    c.setLineWidth(0.5)

    # Assinatura esquerda — responsável
    c.line(12*mm, sig_y, 12*mm + sig_w, sig_y)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7)
    c.drawCentredString(12*mm + sig_w / 2, sig_y - 4*mm, responsavel or 'Responsável pela Solicitação')
    c.setFont('Helvetica-Bold', 6.5)
    c.drawCentredString(12*mm + sig_w / 2, sig_y - 8*mm, 'SOLICITANTE')

    # Assinatura direita — recebedor
    c.line(w - 12*mm - sig_w, sig_y, w - 12*mm, sig_y)
    c.setFont('Helvetica', 7)
    c.drawCentredString(w - 12*mm - sig_w / 2, sig_y - 4*mm, '_________________________________')
    c.setFont('Helvetica-Bold', 6.5)
    c.drawCentredString(w - 12*mm - sig_w / 2, sig_y - 8*mm, 'RESPONSÁVEL PELO RECEBIMENTO')

    # ── RODAPÉ ──────────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7)
    c.drawCentredString(w / 2, 10*mm,
        f'SIPAT — Termo de Recebimento {solicitacao.codigo} — Gerado em {gerado_em}')

    c.save()
    return resp


# ────────────────────────────────────────────────────────────────
# RELATÓRIO DE RECEBIMENTOS (HTML com filtros + impressão)
# ────────────────────────────────────────────────────────────────

@login_required
def relatorio_recebimentos(request):
    from datetime import datetime, date

    contrato_f   = request.GET.get('contrato', '').strip()
    status_f     = request.GET.get('status', '').strip()   # 'recebida' | 'pendente' | ''
    data_ini_str = request.GET.get('data_ini', '').strip()
    data_fim_str = request.GET.get('data_fim', '').strip()

    remessas = (
        BensEnviados.objects
        .select_related(
            'item_enviado__solicitacao__contrato__supplier_contract',
            'item_enviado__bem__efisco',
        )
        .order_by('-data_envio')
    )

    if contrato_f:
        remessas = remessas.filter(item_enviado__solicitacao__contrato_id=contrato_f)

    if status_f == 'recebida':
        remessas = remessas.filter(recebida=True)
    elif status_f == 'pendente':
        remessas = remessas.filter(recebida=False)

    data_ini = data_fim = None
    try:
        if data_ini_str:
            data_ini = datetime.strptime(data_ini_str, '%Y-%m-%d').date()
            remessas = remessas.filter(data_envio__date__gte=data_ini)
        if data_fim_str:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            remessas = remessas.filter(data_envio__date__lte=data_fim)
    except ValueError:
        pass

    contratos = Contrato.objects.filter(
        contrato_soli_saldoativo__isnull=False
    ).distinct().order_by('contrato')

    total       = remessas.count()
    total_rec   = remessas.filter(recebida=True).count()
    total_pend  = remessas.filter(recebida=False).count()
    qtd_total   = remessas.aggregate(t=Sum('quantidade_enviada'))['t'] or 0
    qtd_recebida = remessas.filter(recebida=True).aggregate(t=Sum('quantidade_enviada'))['t'] or 0

    return render(request, 'dimms/saldo_ativo/relatorio_recebimentos.html', {
        'remessas':     remessas,
        'contratos':    contratos,
        'contrato_f':   contrato_f,
        'status_f':     status_f,
        'data_ini_str': data_ini_str,
        'data_fim_str': data_fim_str,
        'total':        total,
        'total_rec':    total_rec,
        'total_pend':   total_pend,
        'qtd_total':    qtd_total,
        'qtd_recebida': qtd_recebida,
        'gerado_em':    timezone.localtime(timezone.now()).strftime('%d/%m/%Y às %H:%M'),
    })
