# BIBLIOTECAS PADRÃO PYTHON
import os
import urllib.request
from io import BytesIO

# DJANGO
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders

# BIBLIOTECAS EXTERNAS
import qrcode
from qrcode.constants import ERROR_CORRECT_M

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import ImageReader

# MODELOS DO PROJETO
from ..models import *
from ..utils import *
from ..forms import *

def artifacts(request):
    artifacts_list = Artifacts.objects.all().order_by('-id')[:10]

    context = {
        'total_artifacts': Artifacts.objects.count(),
        'recent_artifacts': artifacts_list,
    }
    return render(request, 'dimms/artifacts.html', context)