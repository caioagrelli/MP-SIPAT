# bibliotecas do django
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings

# importações do código
from accounts.views import management_required
from ..models import InfoUA
from ..forms import AvisoForm
from ..services import montar_dashboard_usuario
from dimms.models import Estoque, Solicitacao
from dimrcbp.models import BensPermanentes

# ====================================================
# VIEWS CENTRAIS DO SIPAT (DIRECIONAMENTO DE PÁGINAS)
# ====================================================



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
@management_required
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
