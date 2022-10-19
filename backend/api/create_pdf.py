from io import BytesIO

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def create_shopping_cart_pdf(ingredients):
    pdf = BytesIO()
    pdf_obj = canvas.Canvas(pdf)
    arial = TTFont('Arial', 'arial.ttf')
    pdfmetrics.registerFont(arial)
    pdf_obj.setFont('Arial', 14)
    line_num = 760
    for ingredient in ingredients:
        pdf_obj.drawString(
            100,
            line_num,
            (f'{ingredient["ingredient__name"]} - '
             f'{ingredient["amount"]} '
             f'{ingredient["ingredient__measurement_unit"]}'),
        )
        line_num -= 20
    pdf_obj.showPage()
    pdf_obj.save()
    pdf.seek(0)
    return pdf
