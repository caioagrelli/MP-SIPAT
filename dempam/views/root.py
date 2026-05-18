# bibliotecas do django
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect
from django.conf import settings

# importações do código
from ..models import SetorDEMPAM
from dimms.models import Estoque, Solicitacao

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
    return render(request, 'global/home.html')
  
  
''' Homepage'''
# pagina principal do dempam
@login_required
def homepage(request):
    return render(request, 'dempam/homepage.html', {
        'total_setores': SetorDEMPAM.objects.count(),
        'total_consumo': Estoque.objects.count(),
        'total_pendencias': Solicitacao.objects.filter(situation='ATENDIMENTO').count(),
    })
