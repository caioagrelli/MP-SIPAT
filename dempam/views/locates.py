# bibliotecas do django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404

# importações do código
from ..forms import CircunscricaoPredioForm
from ..models import CircunscricaoPredio, InfoUA

# ============================================
# VIEWS DOS LOCAIS (PRÉDIOS E CIRCUNSCRIÇÕES)
# ============================================



''' FUNÇÕES PRINCIPAIS DO SIPAT'''
# homepage dos locais (prédios e circunscrições)
@login_required
def locate_homepage(request):
    query = request.GET.get('q', '').strip()
    meso_filter = request.GET.get('meso', '').strip()

    circunscricoes = CircunscricaoPredio.objects.annotate(
        total_uas=Count('circunscricoes_predios')
    ).order_by('local')

    if query:
        circunscricoes = circunscricoes.filter(Q(local__icontains=query))

    if meso_filter:
        circunscricoes = circunscricoes.filter(meso=meso_filter)

    mesoregiones = CircunscricaoPredio.objects.exclude(meso='').values_list('meso', flat=True).distinct().order_by('meso')

    context = {
        'circunscricoes': circunscricoes,
        'query': query,
        'meso_filter': meso_filter,
        'mesoregiones': mesoregiones,
    }
    return render(request, 'dempam/locates/locate_homepage.html', context)

@login_required
def predio_detail(request, pk):
    predio = get_object_or_404(CircunscricaoPredio, pk=pk)
    uas = predio.circunscricoes_predios.all().order_by('ua')
    return render(request, 'dempam/locates/predio_detail.html', {
        'predio': predio,
        'uas': uas,
    })


# Cadastrar nova circunscrição/prédio
@login_required
def locate_add(request):
    if request.method == 'POST':
        form = CircunscricaoPredioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Circunscrição/Prédio cadastrado com sucesso.')
            return redirect('dempam:locate_add')
    else:
        form = CircunscricaoPredioForm()

    context = {
        'form': form,
        'page_title': 'Cadastrar Circunscrição / Prédio',
        'button_label': 'Salvar',
    }
    return render(request, 'dempam/locates/locate_add.html', context)

# Editar circunscrição/prédio existente
'''@login_required
def locate_update(request, pk):
    circunscricao = get_object_or_404(CircunscricaoPredio, pk=pk)

    if request.method == 'POST':
        form = CircunscricaoPredioForm(request.POST, instance=circunscricao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Circunscrição/Prédio atualizado com sucesso.')
            return redirect('dempam:locate_add')
    else:
        form = CircunscricaoPredioForm(instance=circunscricao)

    context = {
        'form': form,
        'obj': circunscricao,
        'page_title': 'Editar Circunscrição / Prédio',
        'button_label': 'Atualizar',
    }
    return render(request, 'dempam/locate/locate_add.html', context)'''