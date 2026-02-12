from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect

def root(request):
    if request.user.is_authenticated:
        return redirect("homepage") # página quando o usuario estiver logado:
    return redirect("login")  #caso não manda pra tela de login

@login_required
def homepage(request):
    return render(request, 'sipat/homepage.html')
    
@login_required
def bensconsumo(request):
    return render(request, 'sipat/consumo.html')

@login_required
def benspermanentes(request):
    return render(request, 'sipat/permanentes.html')

@login_required
def setores(request):
    return render(request, 'sipat/setores.html')

