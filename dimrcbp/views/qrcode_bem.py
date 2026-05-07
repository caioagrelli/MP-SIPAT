from io import BytesIO

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from dimrcbp.models import BensPermanentes


@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def qrcode_bem(request, tombo):
    bem = get_object_or_404(BensPermanentes, tombo=tombo)

    url = request.build_absolute_uri(
        reverse('dimrcbp:bem_detalhe_admin', args=[bem.tombo])
    )

    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=10, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buf = BytesIO()
    img.save(buf, format='PNG')
    return HttpResponse(buf.getvalue(), content_type='image/png')
