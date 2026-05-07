from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

from dimrcbp.models import Catalogo, Description, Type, Groups


@login_required
def catalogo_lista(request):
    qs = Catalogo.objects.select_related(
        'description', 'description__type', 'description__type__gruop'
    )

    q_efisco    = request.GET.get('efisco', '').strip()
    q_descricao = request.GET.get('descricao', '').strip()
    q_grupo     = request.GET.get('grupo', '').strip()
    q_tipo      = request.GET.get('tipo', '').strip()

    if q_efisco:
        qs = qs.filter(efisco__icontains=q_efisco)
    if q_descricao:
        qs = qs.filter(description__description__icontains=q_descricao)
    if q_grupo:
        qs = qs.filter(description__type__gruop__pk=q_grupo)
    if q_tipo:
        qs = qs.filter(description__type__pk=q_tipo)

    grupos = Groups.objects.all().order_by('group')
    tipos  = Type.objects.all().order_by('type')

    return render(request, 'dimrcbp/catalogo_lista.html', {
        'itens':   qs,
        'grupos':  grupos,
        'tipos':   tipos,
        'filtros': {
            'efisco':    q_efisco,
            'descricao': q_descricao,
            'grupo':     q_grupo,
            'tipo':      q_tipo,
        },
    })


@login_required
def catalogo_detalhe(request, pk):
    item = get_object_or_404(
        Catalogo.objects.select_related(
            'description', 'description__type', 'description__type__gruop'
        ),
        pk=pk,
    )
    return render(request, 'dimrcbp/catalogo_detalhe.html', {'item': item})


@login_required
@permission_required('dimrcbp.add_catalogo', raise_exception=True)
def catalogo_criar(request):
    grupos      = Groups.objects.all().order_by('group')
    tipos       = Type.objects.all().order_by('type')
    descricoes  = Description.objects.select_related('type').order_by('description')

    erros = {}

    if request.method == 'POST':
        efisco    = request.POST.get('efisco', '').strip()
        desc_pk   = request.POST.get('description', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        value     = request.POST.get('value', '').strip() or None
        foto      = request.FILES.get('photo')

        if not efisco:
            erros['efisco'] = 'Campo obrigatório.'
        elif Catalogo.objects.filter(efisco=efisco).exists():
            erros['efisco'] = 'Já existe um item com este código Efisco.'
        if not desc_pk:
            erros['description'] = 'Campo obrigatório.'

        if not erros:
            item = Catalogo(
                efisco=efisco,
                description=get_object_or_404(Description, pk=desc_pk),
                descricao=descricao,
                value=value,
            )
            if foto:
                item.photo = foto
            item.save()
            messages.success(request, f'Item "{item}" adicionado ao catálogo.')
            return redirect('dimrcbp:catalogo_detalhe', pk=item.pk)

    return render(request, 'dimrcbp/catalogo_form.html', {
        'acao':       'Cadastrar',
        'grupos':     grupos,
        'tipos':      tipos,
        'descricoes': descricoes,
        'erros':      erros,
        'val': {
            'efisco':      request.POST.get('efisco', ''),
            'description': request.POST.get('description', ''),
            'descricao':   request.POST.get('descricao', ''),
            'value':       request.POST.get('value', ''),
        },
    })


@login_required
@permission_required('dimrcbp.change_catalogo', raise_exception=True)
def catalogo_editar(request, pk):
    item = get_object_or_404(Catalogo, pk=pk)

    grupos     = Groups.objects.all().order_by('group')
    tipos      = Type.objects.all().order_by('type')
    descricoes = Description.objects.select_related('type').order_by('description')

    erros = {}

    if request.method == 'POST':
        efisco    = request.POST.get('efisco', '').strip()
        desc_pk   = request.POST.get('description', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        value     = request.POST.get('value', '').strip() or None
        foto      = request.FILES.get('photo')

        if not efisco:
            erros['efisco'] = 'Campo obrigatório.'
        elif Catalogo.objects.filter(efisco=efisco).exclude(pk=pk).exists():
            erros['efisco'] = 'Já existe outro item com este código Efisco.'
        if not desc_pk:
            erros['description'] = 'Campo obrigatório.'

        if not erros:
            item.efisco      = efisco
            item.description = get_object_or_404(Description, pk=desc_pk)
            item.descricao   = descricao
            item.value       = value
            if foto:
                item.photo = foto
            item.save()
            messages.success(request, 'Catálogo atualizado com sucesso.')
            return redirect('dimrcbp:catalogo_detalhe', pk=item.pk)

    src = request.POST if request.method == 'POST' else None
    return render(request, 'dimrcbp/catalogo_form.html', {
        'acao':       'Editar',
        'item':       item,
        'grupos':     grupos,
        'tipos':      tipos,
        'descricoes': descricoes,
        'erros':      erros,
        'val': {
            'efisco':      src.get('efisco',      item.efisco)      if src else item.efisco,
            'description': src.get('description', str(item.description_id)) if src else str(item.description_id),
            'descricao':   src.get('descricao',   item.descricao)   if src else item.descricao,
            'value':       src.get('value',       str(item.value or '')) if src else str(item.value or ''),
        },
    })


@login_required
@permission_required('dimrcbp.delete_catalogo', raise_exception=True)
def catalogo_excluir(request, pk):
    item = get_object_or_404(Catalogo, pk=pk)

    if request.method == 'POST':
        nome = str(item)
        item.delete()
        messages.success(request, f'Item "{nome}" excluído do catálogo.')
        return redirect('dimrcbp:catalogo_lista')

    return render(request, 'dimrcbp/catalogo_excluir.html', {'item': item})
