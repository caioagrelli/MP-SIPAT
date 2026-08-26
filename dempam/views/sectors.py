# Importações do Django
import os
from io import BytesIO

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, ProtectedError, Case, When, Value, IntegerField
from django.views.decorators.http import require_POST
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.staticfiles import finders
from django.urls import reverse

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

# Importações do código
from ..models import SetorDEMPAM, LocalizacaoDEMPAM
from ..forms import SetorDEMPAMForm, LocalizacaoDEMPAMForm
from ..utils import TipoSetor
from dimms.models import Estoque
from dimrcbp.models import BensPermanentes

# =========================================
# VIEWS DAS LOZALIZAÇÕES (SETORES E SALAS)
# =========================================


def _ordenar_por_corredor(qs):
    # localizações com corredor definido vêm primeiro, agrupadas e ordenadas por
    # corredor/estante/prateleira; o restante (pallets sem corredor) vem depois
    return qs.annotate(
        sem_corredor=Case(
            When(corredor__isnull=True, then=Value(1)),
            When(corredor='', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('sem_corredor', 'corredor', 'estante', 'prateleira', 'prateleira_pallet')



''' Funções para setores e salas '''
@login_required
def sector_homepage(request):
    setores = SetorDEMPAM.objects.all()
    localizacoes = LocalizacaoDEMPAM.objects.select_related('setor_sala').all()
    total_prateleira = localizacoes.filter(tipo_localizacao='PRATELEIRA').count()
    total_pallet = localizacoes.filter(tipo_localizacao='PALLET').count()

    query = request.GET.get('q', '').strip()
    tipo_f = request.GET.get('tipo', '').strip()

    if query:
        localizacoes = localizacoes.filter(
            Q(prateleira_pallet__icontains=query) |
            Q(setor_sala__setor__icontains=query) |
            Q(corredor__icontains=query)
        )
    if tipo_f:
        localizacoes = localizacoes.filter(tipo_localizacao=tipo_f)

    localizacoes = _ordenar_por_corredor(localizacoes)

    if request.method == 'POST':
        if 'setor_submit' in request.POST:
            form_setor = SetorDEMPAMForm(request.POST)
            form_localizacao = LocalizacaoDEMPAMForm()
            if form_setor.is_valid():
                # Validação de setor duplicado
                setor_nome = form_setor.cleaned_data['setor']
                if SetorDEMPAM.objects.filter(setor=setor_nome).exists():
                    messages.error(request, 'Este setor já está cadastrado.')
                else:
                    form_setor.save()
                    messages.success(request, 'Setor cadastrado com sucesso.')
                return redirect('dempam:sector_homepage')

        elif 'localizacao_submit' in request.POST:
            form_setor = SetorDEMPAMForm()
            form_localizacao = LocalizacaoDEMPAMForm(request.POST)
            if form_localizacao.is_valid():
                form_localizacao.save()
                messages.success(request, 'Localização cadastrada com sucesso.')
                return redirect('dempam:sector_homepage')
    
    else:
        form_setor = SetorDEMPAMForm()
        form_localizacao = LocalizacaoDEMPAMForm()

    return render(request, 'dempam/sectors/sector_homepage.html', {
        'setores': setores,
        'localizacoes': localizacoes,
        'total_localizacoes': LocalizacaoDEMPAM.objects.count(),
        'total_prateleira': total_prateleira,
        'total_pallet': total_pallet,
        'form_setor': form_setor,
        'form_localizacao': form_localizacao,
        'query': query,
        'tipo_f': tipo_f,
    })

@login_required
def sector_add(request):
    if request.method == 'POST':
        form = SetorDEMPAMForm(request.POST)
        if form.is_valid():
            setor_nome = form.cleaned_data['setor']
            if SetorDEMPAM.objects.filter(setor=setor_nome).exists():
                messages.error(request, 'Este setor já está cadastrado.')
            else:
                form.save()
                messages.success(request, 'Setor cadastrado com sucesso.')
                return redirect('dempam:sector_homepage')
    else:
        form = SetorDEMPAMForm()
    return render(request, 'dempam/sectors/sector_add.html', {'form': form})


@login_required
def sector_edit(request, pk):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    if request.method == 'POST':
        form = SetorDEMPAMForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Setor atualizado com sucesso.')
            return redirect('dempam:sector_detail', pk=setor.pk)
    else:
        form = SetorDEMPAMForm(instance=setor)
    return render(request, 'dempam/sectors/sector_add.html', {'form': form, 'setor': setor, 'editando': True})


@login_required
@require_POST
def sector_delete(request, pk):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    try:
        setor.delete()
        messages.success(request, 'Setor excluído com sucesso.')
        return redirect('dempam:sector_homepage')
    except ProtectedError:
        messages.error(
            request,
            'Não é possível excluir: existem pallets/prateleiras cadastrados neste setor.',
        )
        return redirect('dempam:sector_detail', pk=setor.pk)


def _montar_navegacao_corredores(setor):
    por_corredor = {}
    qs = (
        setor.localizacao_interna
        .exclude(corredor__isnull=True).exclude(corredor='')
        .order_by('corredor', 'estante', 'prateleira')
    )
    for loc in qs:
        por_corredor.setdefault(loc.corredor, {}).setdefault(loc.estante or '—', []).append(loc)

    corredores_ordenados = sorted(por_corredor.keys(), key=lambda c: (len(c), c))
    navegacao = []
    for corredor in corredores_ordenados:
        estantes_dict = por_corredor[corredor]
        estantes_ordenadas = sorted(estantes_dict.keys(), key=lambda e: (len(e), e))
        estantes = [
            {'estante': estante, 'prateleiras': estantes_dict[estante]}
            for estante in estantes_ordenadas
        ]
        navegacao.append({
            'corredor': corredor,
            'estantes': estantes,
            'total': sum(len(e['prateleiras']) for e in estantes),
        })
    return navegacao


@login_required
def sector_detail(request, pk):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    localizacoes = setor.localizacao_interna.all()
    total_prateleira = localizacoes.filter(tipo_localizacao='PRATELEIRA').count()
    total_pallet = localizacoes.filter(tipo_localizacao='PALLET').count()

    navegacao_corredores = _montar_navegacao_corredores(setor)
    corredores = [grupo['corredor'] for grupo in navegacao_corredores]

    query = request.GET.get('q', '').strip()
    tipo_f = request.GET.get('tipo', '').strip()
    corredor_f = request.GET.get('corredor', '').strip()

    if query:
        localizacoes = localizacoes.filter(
            Q(prateleira_pallet__icontains=query) | Q(corredor__icontains=query)
        )
    if tipo_f:
        localizacoes = localizacoes.filter(tipo_localizacao=tipo_f)
    if corredor_f:
        localizacoes = localizacoes.filter(corredor=corredor_f)

    localizacoes = _ordenar_por_corredor(localizacoes)

    return render(request, 'dempam/sectors/sector_detail.html', {
        'setor': setor,
        'localizacoes': localizacoes,
        'total_localizacoes': setor.localizacao_interna.count(),
        'total_prateleira': total_prateleira,
        'total_pallet': total_pallet,
        'corredores': corredores,
        'navegacao_corredores': navegacao_corredores,
        'query': query,
        'tipo_f': tipo_f,
        'corredor_f': corredor_f,
    })


''' Busca de itens dentro do setor — usada pela caixa de pesquisa "onde está o item" '''
@login_required
def sector_item_search(request, pk):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'resultados': []})

    if setor.tipo == TipoSetor.dimrcbp:
        bens = (
            BensPermanentes.objects
            .filter(locate__setor_sala=setor)
            .filter(
                Q(tombo__icontains=query) |
                Q(description__description__icontains=query) |
                Q(mark__icontains=query) |
                Q(model__icontains=query)
            )
            .select_related('description', 'locate')
            .order_by('tombo')[:30]
        )
        resultados = [
            {
                'efisco': bem.tombo,
                'descricao': str(bem.description),
                'marca': bem.mark or '',
                'quantidade': '1',
                'localizacao': bem.locate.prateleira_pallet,
                'corredor': bem.locate.corredor,
                'estante': bem.locate.estante,
                'prateleira': bem.locate.prateleira,
                'locate_url': reverse('dempam:locate_detail', args=[bem.locate.pk]),
                'corredor_url': (
                    reverse('dempam:corredor_detail', args=[setor.pk, bem.locate.corredor])
                    if bem.locate.corredor else None
                ),
            }
            for bem in bens
        ]
        return JsonResponse({'resultados': resultados[:30]})

    itens = (
        Estoque.objects
        .filter(Q(locate__setor_sala=setor) | Q(outras_localizacoes__setor_sala=setor))
        .filter(
            Q(item_shock__efisco__icontains=query) |
            Q(description_manual__icontains=query) |
            Q(mark__icontains=query)
        )
        .select_related('item_shock', 'locate')
        .prefetch_related('outras_localizacoes')
        .distinct()
        .order_by('description_manual')[:30]
    )

    def _serializar(item, loc):
        return {
            'efisco': item.item_shock.efisco,
            'descricao': item.description_manual or item.item_shock.descricao_efisco,
            'marca': item.mark or '',
            'quantidade': str(item.amount_shock),
            'localizacao': loc.prateleira_pallet,
            'corredor': loc.corredor,
            'estante': loc.estante,
            'prateleira': loc.prateleira,
            'locate_url': reverse('dempam:locate_detail', args=[loc.pk]),
            'corredor_url': (
                reverse('dempam:corredor_detail', args=[setor.pk, loc.corredor])
                if loc.corredor else None
            ),
        }

    # cada item pode aparecer mais de uma vez: uma linha por localização (principal
    # ou "outras localizações") que pertença a este setor
    resultados = []
    for item in itens:
        if item.locate_id and item.locate.setor_sala_id == setor.pk:
            resultados.append(_serializar(item, item.locate))
        for loc in item.outras_localizacoes.all():
            if loc.setor_sala_id == setor.pk:
                resultados.append(_serializar(item, loc))

    return JsonResponse({'resultados': resultados[:30]})


@login_required
def locate_detail(request, pk):
    localizacao = get_object_or_404(LocalizacaoDEMPAM, pk=pk)

    if localizacao.setor_sala and localizacao.setor_sala.tipo == TipoSetor.dimrcbp:
        bens = (
            BensPermanentes.objects
            .filter(locate=localizacao)
            .select_related('description', 'supllier')
            .order_by('tombo')
        )
        return render(request, 'dempam/sectors/locate_detail.html', {
            'localizacao': localizacao,
            'bens': bens,
            'is_dimrcbp': True,
        })

    itens = (
        Estoque.objects
        .filter(Q(locate=localizacao) | Q(outras_localizacoes=localizacao))
        .select_related('item_shock')
        .distinct()
    )
    total_qtd = sum(i.amount_shock for i in itens)
    return render(request, 'dempam/sectors/locate_detail.html', {
        'localizacao': localizacao,
        'itens': itens,
        'total_qtd': total_qtd,
        'is_dimrcbp': False,
    })


@login_required
def sector_locate_add(request):
    if request.method == 'POST':
        form = LocalizacaoDEMPAMForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Localização cadastrada com sucesso.')
            return redirect('dempam:sector_homepage')
    else:
        form = LocalizacaoDEMPAMForm()
    return render(request, 'dempam/sectors/sector_locate_add.html', {'form': form})


@login_required
def locate_edit(request, pk):
    localizacao = get_object_or_404(LocalizacaoDEMPAM, pk=pk)
    if request.method == 'POST':
        form = LocalizacaoDEMPAMForm(request.POST, instance=localizacao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Localização atualizada com sucesso.')
            return redirect('dempam:locate_detail', pk=localizacao.pk)
    else:
        form = LocalizacaoDEMPAMForm(instance=localizacao)
    return render(request, 'dempam/sectors/sector_locate_add.html', {
        'form': form, 'localizacao': localizacao, 'editando': True,
    })


def _tamanho_max_fonte(c, texto, largura_max, fonte='Helvetica-Bold', tamanho_max=420, tamanho_min=120):
    tamanho = tamanho_max
    while tamanho > tamanho_min and c.stringWidth(texto, fonte, tamanho) > largura_max:
        tamanho -= 4
    return tamanho


def _gerar_qrcode_reader(url):
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=10, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='#1e2d42', back_color='white')
    buf = BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)
    return ImageReader(buf)


def _desenhar_cartaz_corredor(c, w, h, setor, corredor, qr_reader):
    altura_cabecalho = 55 * mm

    # ── faixa superior com identidade do SIPAT (bem maior) ──
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(0, h - altura_cabecalho, w, altura_cabecalho, fill=1, stroke=0)

    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        c.drawImage(ImageReader(logo_path), 15 * mm, h - 44 * mm, width=26 * mm, height=26 * mm, mask='auto')

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 18)
    c.drawString(48 * mm, h - 21 * mm, 'MINISTÉRIO PÚBLICO DE PERNAMBUCO')
    c.setFont('Helvetica', 12)
    c.drawString(48 * mm, h - 30 * mm, 'SIPAT — Sistema Integrado Patrimonial')
    c.setFont('Helvetica-Bold', 12)
    c.drawString(48 * mm, h - 39 * mm, setor.setor.upper())

    # ── rótulo "CORREDOR" ──
    c.setFillColor(colors.HexColor('#2563eb'))
    c.setFont('Helvetica-Bold', 28)
    rotulo = 'CORREDOR'
    lw = c.stringWidth(rotulo, 'Helvetica-Bold', 28)
    c.drawString((w - lw) / 2, h - altura_cabecalho - 24 * mm, rotulo)

    # ── código do corredor bem grande, centralizado ──
    largura_disponivel = w - 30 * mm
    tamanho = _tamanho_max_fonte(c, corredor, largura_disponivel)
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.setFont('Helvetica-Bold', tamanho)
    lw2 = c.stringWidth(corredor, 'Helvetica-Bold', tamanho)
    baseline_y = h / 2 - tamanho * 0.32
    c.drawString((w - lw2) / 2, baseline_y, corredor)

    # ── qrcode maior, no canto inferior direito, com borda própria ──
    qr_size = 34 * mm
    qr_margin = 14 * mm
    qr_pad = 3 * mm
    qr_x = w - qr_margin - qr_size
    qr_y = qr_margin

    c.setStrokeColor(colors.HexColor('#2563eb'))
    c.setLineWidth(1.6)
    c.rect(qr_x - qr_pad, qr_y - qr_pad, qr_size + 2 * qr_pad, qr_size + 2 * qr_pad, fill=0, stroke=1)
    c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size, mask='auto')


def _desenhar_etiqueta_estante(c, w, h, setor, codigo_estante, qr_reader):
    altura_cabecalho = 26 * mm

    # ── faixa superior com identidade do SIPAT ──
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(0, h - altura_cabecalho, w, altura_cabecalho, fill=1, stroke=0)

    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        c.drawImage(ImageReader(logo_path), 8 * mm, h - altura_cabecalho + 3 * mm, width=20 * mm, height=20 * mm, mask='auto')

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(33 * mm, h - 10 * mm, 'MINISTÉRIO PÚBLICO DE PERNAMBUCO')
    c.setFont('Helvetica', 8)
    c.drawString(33 * mm, h - 16 * mm, 'SIPAT — Sistema Integrado Patrimonial')
    c.setFont('Helvetica-Bold', 8)
    c.drawString(33 * mm, h - 22 * mm, setor.setor.upper())

    # ── corpo: rótulo "ESTANTE" + código grande à esquerda, QR à direita ──
    corpo_top = h - altura_cabecalho
    qr_size = 46 * mm
    qr_margin = 8 * mm

    c.setFillColor(colors.HexColor('#2563eb'))
    c.setFont('Helvetica-Bold', 13)
    rotulo = 'ESTANTE'
    label_y = corpo_top - 12 * mm
    c.drawString(14 * mm, label_y, rotulo)

    # código grande, centralizado na área abaixo do rótulo
    area_top = label_y - 8 * mm
    area_bottom = 12 * mm
    largura_disponivel = w - qr_size - qr_margin * 2 - 28 * mm
    tamanho = _tamanho_max_fonte(c, codigo_estante, largura_disponivel, tamanho_max=100, tamanho_min=60)
    cap_height = tamanho * 0.72 / 2.834  # aprox. altura de caixa-alta em mm
    baseline_y = area_bottom + (area_top - area_bottom - cap_height) / 2
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.setFont('Helvetica-Bold', tamanho)
    c.drawString(14 * mm, baseline_y, codigo_estante)

    # ── qrcode no canto inferior direito, com borda própria ──
    qr_x = w - qr_margin - qr_size
    qr_y = qr_margin
    qr_pad = 2.5 * mm

    c.setStrokeColor(colors.HexColor('#2563eb'))
    c.setLineWidth(1.4)
    c.rect(qr_x - qr_pad, qr_y - qr_pad, qr_size + 2 * qr_pad, qr_size + 2 * qr_pad, fill=0, stroke=1)
    c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size, mask='auto')


''' Imprimir uma etiqueta em meia folha A4 por estante, com QR code pra página da estante '''
@login_required
def imprimir_estantes(request, pk):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    base = (
        setor.localizacao_interna
        .exclude(corredor__isnull=True).exclude(corredor='')
        .exclude(estante__isnull=True).exclude(estante='')
    )

    pares = sorted(set(base.values_list('corredor', 'estante')), key=lambda ce: (len(ce[0]), ce[0], len(ce[1]), ce[1]))

    corredores_sel = [c for c in request.GET.getlist('corredor') if c]
    if corredores_sel:
        pares = [(c, e) for c, e in pares if c in corredores_sel]

    if not pares:
        messages.error(request, 'Não há estantes cadastradas neste setor para imprimir.')
        return redirect('dempam:sector_detail', pk=setor.pk)

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="estantes_{setor.pk}.pdf"'

    # duas etiquetas por folha A4 (uma em cada metade), pra imprimir e cortar ao meio
    w, h = A4
    meia_h = h / 2
    c = rl_canvas.Canvas(resp, pagesize=A4)

    for i in range(0, len(pares), 2):
        lote = pares[i:i + 2]

        for posicao, (corredor, estante) in enumerate(lote):
            codigo_estante = f'{corredor}{estante}'
            url = request.build_absolute_uri(
                reverse('dempam:estante_detail', args=[setor.pk, corredor, estante])
            )
            qr_reader = _gerar_qrcode_reader(url)
            c.saveState()
            if posicao == 0:
                c.translate(0, meia_h)
            _desenhar_etiqueta_estante(c, w, meia_h, setor, codigo_estante, qr_reader)
            c.restoreState()

        # linha tracejada indicando onde cortar
        c.saveState()
        c.setDash(4, 3)
        c.setStrokeColor(colors.HexColor('#9aa5bd'))
        c.setLineWidth(0.8)
        c.line(0, meia_h, w, meia_h)
        c.restoreState()
        c.setFont('Helvetica', 7)
        c.setFillColor(colors.HexColor('#9aa5bd'))
        c.drawCentredString(w / 2, meia_h + 5, '✂ corte aqui')

        c.showPage()

    c.save()
    return resp


''' Imprimir um cartaz grande por corredor, para afixar fisicamente no setor '''
@login_required
def imprimir_corredores(request, pk):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    base = setor.localizacao_interna.exclude(corredor__isnull=True).exclude(corredor='')

    corredores = sorted(set(base.values_list('corredor', flat=True)), key=lambda c: (len(c), c))

    selecionados = [c for c in request.GET.getlist('corredor') if c]
    if selecionados:
        corredores = [c for c in corredores if c in selecionados]

    if not corredores:
        messages.error(request, 'Não há corredores cadastrados neste setor para imprimir.')
        return redirect('dempam:sector_detail', pk=setor.pk)

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="corredores_{setor.pk}.pdf"'

    w, h = A4
    c = rl_canvas.Canvas(resp, pagesize=A4)

    for corredor in corredores:
        url = request.build_absolute_uri(
            reverse('dempam:corredor_detail', args=[setor.pk, corredor])
        )
        qr_reader = _gerar_qrcode_reader(url)
        _desenhar_cartaz_corredor(c, w, h, setor, corredor, qr_reader)
        c.showPage()

    c.save()
    return resp


''' Página (acessada pelo QR code do cartaz) com o conteúdo de todas as prateleiras de um corredor,
organizada por estante e depois por prateleira '''
@login_required
def corredor_detail(request, pk, corredor):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    localizacoes = (
        setor.localizacao_interna
        .filter(corredor=corredor)
        .order_by('estante', 'prateleira')
    )
    if not localizacoes.exists():
        raise Http404('Corredor não encontrado.')

    is_dimrcbp = setor.tipo == TipoSetor.dimrcbp

    por_estante = {}
    todos_itens = []
    total_itens = 0
    for loc in localizacoes:
        if is_dimrcbp:
            itens = list(
                BensPermanentes.objects
                .filter(locate=loc)
                .select_related('description')
                .order_by('tombo')
            )
        else:
            itens = list(
                Estoque.objects
                .filter(Q(locate=loc) | Q(outras_localizacoes=loc))
                .select_related('item_shock')
                .distinct()
            )
        total_itens += len(itens)
        por_estante.setdefault(loc.estante or '—', []).append({'localizacao': loc, 'itens': itens})
        for item in itens:
            todos_itens.append({'item': item, 'localizacao': loc})

    estantes_ordenadas = sorted(por_estante.keys(), key=lambda e: (len(e), e))
    estantes = [
        {
            'estante': estante,
            'prateleiras': por_estante[estante],
            'total_prateleiras': len(por_estante[estante]),
            'com_itens': sum(1 for p in por_estante[estante] if p['itens']),
            'total_itens': sum(len(p['itens']) for p in por_estante[estante]),
        }
        for estante in estantes_ordenadas
    ]

    grupos_com_itens = [p for grupo in estantes for p in grupo['prateleiras'] if p['itens']]
    todos_itens.sort(key=lambda x: (x['localizacao'].estante or '', x['localizacao'].prateleira or ''))

    return render(request, 'dempam/sectors/corredor_detail.html', {
        'setor': setor,
        'corredor': corredor,
        'estantes': estantes,
        'grupos_com_itens': grupos_com_itens,
        'todos_itens': todos_itens,
        'total_itens': total_itens,
        'total_prateleiras': localizacoes.count(),
        'is_dimrcbp': is_dimrcbp,
    })


''' Página (acessada pelo QR code da etiqueta) com o conteúdo de uma estante específica
(um corredor + uma estante), organizada por prateleira '''
@login_required
def estante_detail(request, pk, corredor, estante):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    localizacoes = (
        setor.localizacao_interna
        .filter(corredor=corredor, estante=estante)
        .order_by('prateleira')
    )
    if not localizacoes.exists():
        raise Http404('Estante não encontrada.')

    is_dimrcbp = setor.tipo == TipoSetor.dimrcbp

    grupos = []
    total_itens = 0
    for loc in localizacoes:
        if is_dimrcbp:
            itens = list(
                BensPermanentes.objects
                .filter(locate=loc)
                .select_related('description')
                .order_by('tombo')
            )
        else:
            itens = list(
                Estoque.objects
                .filter(Q(locate=loc) | Q(outras_localizacoes=loc))
                .select_related('item_shock')
                .distinct()
            )
        total_itens += len(itens)
        grupos.append({'localizacao': loc, 'itens': itens})

    return render(request, 'dempam/sectors/estante_detail.html', {
        'setor': setor,
        'corredor': corredor,
        'estante': estante,
        'codigo_estante': f'{corredor}{estante}',
        'grupos': grupos,
        'total_prateleiras': localizacoes.count(),
        'total_itens': total_itens,
        'is_dimrcbp': is_dimrcbp,
    })


@login_required
@require_POST
def locate_delete(request, pk):
    localizacao = get_object_or_404(LocalizacaoDEMPAM, pk=pk)
    setor_pk = localizacao.setor_sala_id
    try:
        localizacao.delete()
        messages.success(request, 'Localização excluída com sucesso.')
    except ProtectedError:
        messages.error(
            request,
            'Não é possível excluir: existem itens de estoque vinculados a esta localização.',
        )
        return redirect('dempam:locate_detail', pk=pk)
    if setor_pk:
        return redirect('dempam:sector_detail', pk=setor_pk)
    return redirect('dempam:sector_homepage')

