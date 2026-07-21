from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from accounts.models import Feedback, StatusFeedback
from accounts.views import management_required


@management_required
def lista_feedback(request):
    tipo   = request.GET.get('tipo', '').strip()
    status = request.GET.get('status', '').strip()
    query  = request.GET.get('q', '').strip()

    qs = Feedback.objects.select_related('user').order_by('-criado_em')

    if tipo in ('bug', 'sugestao'):
        qs = qs.filter(tipo=tipo)
    if status in StatusFeedback.values:
        qs = qs.filter(status=status)
    if query:
        qs = qs.filter(
            Q(descricao__icontains=query)
            | Q(pagina__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
        )

    total       = Feedback.objects.count()
    total_bug   = Feedback.objects.filter(tipo='bug').count()
    total_sug   = Feedback.objects.filter(tipo='sugestao').count()
    total_aberto = Feedback.objects.exclude(status=StatusFeedback.finalizado).exclude(status=StatusFeedback.recusado).count()

    return render(request, 'access/feedback_lista.html', {
        'feedbacks': qs,
        'tipo': tipo,
        'status': status,
        'query': query,
        'total': total,
        'total_bug': total_bug,
        'total_sug': total_sug,
        'total_aberto': total_aberto,
        'status_choices': StatusFeedback.choices,
    })


@management_required
@require_POST
def atualizar_status(request, pk):
    novo_status = request.POST.get('status', '').strip()
    resolucao   = request.POST.get('resolucao', '').strip()
    if novo_status not in StatusFeedback.values:
        return JsonResponse({'ok': False, 'error': 'Status inválido.'}, status=400)

    fb = get_object_or_404(Feedback, pk=pk)
    fb.status = novo_status
    campos = ['status']
    if resolucao:
        fb.resolucao = resolucao
        campos.append('resolucao')
    fb.save(update_fields=campos)

    return JsonResponse({
        'ok': True,
        'status': fb.status,
        'label': fb.get_status_display(),
        'resolucao': fb.resolucao,
    })


@login_required
@require_POST
def reportar(request):
    tipo      = request.POST.get('tipo', '').strip()
    descricao = request.POST.get('descricao', '').strip()
    pagina    = request.POST.get('pagina', '').strip()[:500]
    imagem    = request.FILES.get('imagem')

    tipos_validos = {t for t, _ in Feedback.TIPO_CHOICES}
    if tipo not in tipos_validos:
        return JsonResponse({'ok': False, 'error': 'Tipo inválido.'}, status=400)
    if not descricao:
        return JsonResponse({'ok': False, 'error': 'Descrição obrigatória.'}, status=400)

    Feedback.objects.create(
        user=request.user,
        tipo=tipo,
        descricao=descricao,
        pagina=pagina,
        imagem=imagem,
    )
    return JsonResponse({'ok': True})
