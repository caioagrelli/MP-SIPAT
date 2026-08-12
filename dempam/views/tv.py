# Importações do Django
import re

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone

# Importações do código
from accounts.views import management_required
from ..models import ConfiguracaoPainelTV
from ..forms import ConfiguracaoPainelTVForm
from ..services import obter_avisos
from dimms.models import Solicitacao
from dimms.utils import StatusTramitacao

# ====================================
# PAINEL DE TV (GESTÃO À VISTA)
# ====================================


def _eh_link_youtube(url):
    return bool(re.search(r'(?:youtube\.com|youtu\.be)', url, re.IGNORECASE))


def _extrair_youtube_id(url):
    if not url:
        return ''
    match = re.search(r'(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})', url)
    return match.group(1) if match else ''


@login_required
def painel_tv(request):
    solicitacoes_aguardando = (
        Solicitacao.objects
        .filter(situation=StatusTramitacao.aguar_separada)
        .select_related('ua_order')
        .order_by('-data_order')
    )
    solicitacoes_separadas = (
        Solicitacao.objects
        .filter(situation=StatusTramitacao.separada)
        .select_related('ua_order')
        .order_by('-data_order')
    )

    config = ConfiguracaoPainelTV.get_config()
    video_url = config.video_url or ''
    youtube_video_id = ''
    video_direto_url = ''
    video_arquivo_url = ''

    if config.video_arquivo:
        video_arquivo_url = config.video_arquivo.url
    elif video_url:
        if _eh_link_youtube(video_url):
            youtube_video_id = _extrair_youtube_id(video_url)
        else:
            video_direto_url = video_url

    context = {
        'agora': timezone.now(),
        'solicitacoes_aguardando': solicitacoes_aguardando[:60],
        'total_aguardando': solicitacoes_aguardando.count(),
        'solicitacoes_separadas': solicitacoes_separadas[:60],
        'total_separadas': solicitacoes_separadas.count(),
        'avisos': obter_avisos(limite=8),
        'youtube_video_id': youtube_video_id,
        'video_direto_url': video_direto_url,
        'video_arquivo_url': video_arquivo_url,
    }
    return render(request, 'dempam/tv/painel.html', context)


''' Configurar o link do vídeo exibido no painel de TV '''
@management_required
def painel_tv_config(request):
    config = ConfiguracaoPainelTV.get_config()
    if request.method == 'POST':
        form = ConfiguracaoPainelTVForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            config = form.save(commit=False)
            config.atualizado_por = request.user
            config.save()
            messages.success(request, 'Vídeo do painel atualizado com sucesso.')
            return redirect('dempam:homepage')
    else:
        form = ConfiguracaoPainelTVForm(instance=config)
    return render(request, 'dempam/tv/config.html', {'form': form, 'config': config})
