# bibliotecas do django
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

# importações do código
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from ..models import InfoUA, Aviso
from ..forms import AvisoForm
from ..services import montar_dashboard_usuario
from dimms.models import Estoque, Solicitacao
from dimrcbp.models import BensPermanentes

# ====================================================
# VIEWS CENTRAIS DO SIPAT (DIRECIONAMENTO DE PÁGINAS)
# ====================================================


def gerencia_dempam_required(view_func):
    """Permite superusuários, staff, ou membros da Gerência DEMPAM — mais restrito
    que management_required (que também libera gestão de usuários/grupos)."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name='Gerência DEMPAM').exists()
        ):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper



''' FUNÇÕES PRINCIPAIS DO SIPAT'''
# destinar paginas
def root(request):
    if request.user.is_authenticated:
        return redirect('home')  # Página quando o usuário estiver logado
    next_url = request.GET.get('next', '')
    login_url = f"{settings.LOGIN_URL}?next={next_url}" if next_url else settings.LOGIN_URL
    return redirect(login_url)

#homepage central (futuramente vai ser um app a parte)
@login_required
def home(request):
    context = montar_dashboard_usuario(request.user)
    return render(request, 'global/home.html', context)
  
  
''' Homepage'''
# pagina principal do dempam
@login_required
def homepage(request):
    return render(request, 'dempam/homepage.html', {
        'total_setores': InfoUA.objects.count(),
        'total_bens_permanentes': BensPermanentes.objects.count(),
        'total_consumo': Estoque.objects.count(),
        'total_pendencias': Solicitacao.objects.filter(situation='ATENDIMENTO').count(),
    })


''' Mural de Avisos '''
# Publicar um novo aviso no mural do DEMPAM (exibido em /home/)
@gerencia_dempam_required
def aviso_criar(request):
    if request.method == 'POST':
        form = AvisoForm(request.POST)
        if form.is_valid():
            aviso = form.save(commit=False)
            aviso.autor = request.user
            aviso.save()
            messages.success(request, 'Aviso publicado no mural com sucesso.')
            return redirect('dempam:homepage')
    else:
        form = AvisoForm()

    return render(request, 'dempam/aviso_form.html', {'form': form})


''' Editar um aviso existente do mural '''
@gerencia_dempam_required
def aviso_editar(request, pk):
    aviso = get_object_or_404(Aviso, pk=pk)
    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aviso atualizado com sucesso.')
            return redirect('dempam:aviso_lista')
    else:
        form = AvisoForm(instance=aviso)

    return render(request, 'dempam/aviso_form.html', {'form': form, 'aviso': aviso, 'editando': True})


''' Listar avisos do mural (para gerenciar/excluir) '''
@gerencia_dempam_required
def aviso_lista(request):
    avisos = Aviso.objects.select_related('autor').all()
    return render(request, 'dempam/aviso_lista.html', {'avisos': avisos, 'now': timezone.now()})


''' Excluir um aviso do mural '''
@gerencia_dempam_required
@require_POST
def aviso_excluir(request, pk):
    aviso = get_object_or_404(Aviso, pk=pk)
    aviso.delete()
    messages.success(request, 'Aviso excluído com sucesso.')
    return redirect('dempam:aviso_lista')
