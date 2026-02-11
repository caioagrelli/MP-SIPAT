from django.shortcuts import render
from django.shortcuts import redirect

def root(request):
    if request.user.is_authenticated:
        return redirect("/admin/") # página quando o usuario estiver logado:
    return redirect("login")  #caso não manda pra tela de login
