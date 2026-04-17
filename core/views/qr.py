"""
core/views/qr.py
QR Code generation views — kept isolated from business logic.
"""
from io import BytesIO

import qrcode
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View


class QRGeneratorView(View):
    template_name = 'qr_generator.html'

    def get(self, request):
        url = request.GET.get('url')
        if 'download' in request.GET and url:
            return self._generate_qr(url, download=True)
        return render(request, self.template_name, {'url': url})

    @staticmethod
    def _generate_qr(url, download=False):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        response = HttpResponse(buffer.getvalue(), content_type="image/png")
        if download:
            response['Content-Disposition'] = 'attachment; filename="trimrr_qr.png"'
        return response


def qr_image_view(request):
    """Inline QR image endpoint used by the preview card."""
    url = request.GET.get('url')
    if not url:
        return HttpResponse(status=400)

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0058be", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")
