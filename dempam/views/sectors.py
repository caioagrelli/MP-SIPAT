# Importações do Django
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Importações do código
from ..models import SetorDEMPAM, LocalizacaoDEMPAM
from ..forms import SetorDEMPAMForm, LocalizacaoDEMPAMForm
from dimms.models import Estoque

# =========================================
# VIEWS DAS LOZALIZAÇÕES (SETORES E SALAS)
# =========================================



''' Funções para setores e salas '''
@login_required
def sector_homepage(request):
    setores = SetorDEMPAM.objects.all()
    localizacoes = LocalizacaoDEMPAM.objects.all()
    total_prateleira = localizacoes.filter(tipo_localizacao='PRATELEIRA').count()
    total_pallet = localizacoes.filter(tipo_localizacao='PALLET').count()

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
        'total_prateleira': total_prateleira,
        'total_pallet': total_pallet,
        'form_setor': form_setor,
        'form_localizacao': form_localizacao
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
def sector_detail(request, pk):
    setor = get_object_or_404(SetorDEMPAM, pk=pk)
    localizacoes = setor.localizacao_interna.all()
    total_prateleira = localizacoes.filter(tipo_localizacao='PRATELEIRA').count()
    total_pallet = localizacoes.filter(tipo_localizacao='PALLET').count()
    return render(request, 'dempam/sectors/sector_detail.html', {
        'setor': setor,
        'localizacoes': localizacoes,
        'total_prateleira': total_prateleira,
        'total_pallet': total_pallet,
    })


@login_required
def locate_detail(request, pk):
    localizacao = get_object_or_404(LocalizacaoDEMPAM, pk=pk)
    itens = localizacao.localizacao_consumo.select_related('item_shock').all()
    total_qtd = sum(i.amount_shock for i in itens)
    return render(request, 'dempam/sectors/locate_detail.html', {
        'localizacao': localizacao,
        'itens': itens,
        'total_qtd': total_qtd,
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

