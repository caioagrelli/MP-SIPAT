from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect



@login_required
def homepage(request):
    return render(request, 'dimms/homepage.html')
