from reportlab.platypus import SimpleDocTemplate, Image
from reportlab.lib.pagesizes import A4

async def create_pdf(images, folder):

    pdf_path = f"{folder}/chapter.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)

    elements = []

    for img in images:
        elements.append(Image(img))

    doc.build(elements)

    return pdf_path
