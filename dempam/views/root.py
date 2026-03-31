# bibliotecas do django
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect

# ====================================================
# VIEWS CENTRAIS DO SIPAT (DIRECIONAMENTO DE PÁGINAS)
# ====================================================



''' FUNÇÕES PRINCIPAIS DO SIPAT'''
# destinar paginas
def root(request):
    if request.user.is_authenticated:
        return redirect('home') # página quando o usuario estiver logado:
    return redirect('login')  #caso não manda pra tela de login

#homepage central (futuramente vai ser um app a parte)
@login_required
def home(request):
    return render(request, 'global/home.html')
  
  
''' Homepage'''
# pagina principal do dempam
@login_required
def homepage(request):
    return render(request, 'dempam/homepage.html')
