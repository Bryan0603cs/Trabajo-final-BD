# reports/pdf_generator.py
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any

from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet


class PDFGenerator:
    """
    Generador de PDFs para TechStore.
    Se usa tanto para facturas como para reportes tabulares.
    """

    @staticmethod
    def _build_doc_buffer() -> (SimpleDocTemplate, BytesIO):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=LETTER,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        return doc, buffer

    @staticmethod
    def _styles():
        styles = getSampleStyleSheet()
        title = styles["Heading1"]
        title.fontName = "Helvetica-Bold"
        title.textColor = colors.HexColor("#1a1a4d")

        h2 = styles["Heading2"]
        h2.fontName = "Helvetica-Bold"
        h2.textColor = colors.HexColor("#333366")
        h2.spaceAfter = 6

        normal = styles["BodyText"]
        normal.fontName = "Helvetica"
        normal.fontSize = 10
        normal.leading = 13

        small = styles["BodyText"]
        small.fontName = "Helvetica"
        small.fontSize = 9
        small.leading = 11

        return {
            "title": title,
            "h2": h2,
            "normal": normal,
            "small": small,
        }

    # ------------------------------------------------------------------ #
    #  FACTURA DE VENTA
    # ------------------------------------------------------------------ #
    @staticmethod
    def factura_venta(data: Dict[str, Any]) -> bytes:
        """
        data:
          venta: dict con ID_VENTA, FECHA, TOTAL, ES_CREDITO
          cliente: dict con NOMBRE_COMPLETO, DOCUMENTO
          detalles: list[dict] con NOMBRE_PROD, CANTIDAD, PRECIO, SUBTOTAL
        """
        doc, buffer = PDFGenerator._build_doc_buffer()
        styles = PDFGenerator._styles()
        elements = []

        venta = data["venta"]
        cliente = data["cliente"]
        detalles = data["detalles"]

        # Encabezado
        elements.append(Paragraph("TechStore - Factura de Venta", styles["title"]))
        elements.append(
            Paragraph(
                f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles["small"],
            )
        )
        elements.append(Spacer(1, 12))

        # Datos generales
        elements.append(Paragraph(f"Número de venta: {venta['ID_VENTA']}", styles["h2"]))
        elements.append(
            Paragraph(
                f"Fecha de la venta: {venta['FECHA'].strftime('%d/%m/%Y')}",
                styles["normal"],
            )
        )
        elements.append(
            Paragraph(f"Tipo de venta: {'CRÉDITO' if venta['ES_CREDITO'] == 'S' else 'CONTADO'}",
                      styles["normal"])
        )
        elements.append(Spacer(1, 12))

        # Datos cliente
        elements.append(Paragraph("Datos del cliente", styles["h2"]))
        elements.append(
            Paragraph(f"Cliente: {cliente['NOMBRE_COMPLETO']}", styles["normal"])
        )
        elements.append(
            Paragraph(f"Documento: {cliente.get('DOCUMENTO', '')}", styles["normal"])
        )
        elements.append(Spacer(1, 12))

        # Tabla detalle
        elements.append(Paragraph("Detalle de productos", styles["h2"]))

        data_table = [["Producto", "Cantidad", "Precio unitario", "Subtotal"]]
        for d in detalles:
            data_table.append(
                [
                    d["NOMBRE_PRODUCTO"],
                    int(d["CANTIDAD"]),
                    f"${d['PRECIO_UNITARIO']:,.0f}",
                    f"${d['SUBTOTAL']:,.0f}",
                ]
            )

        table = Table(data_table, colWidths=[220, 70, 100, 100])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#667eea")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(f"TOTAL: ${venta['TOTAL']:,.0f}", styles["h2"])
        )

        doc.build(elements)
        return buffer.getvalue()

    # ------------------------------------------------------------------ #
    #  REPORTES TABULARES GENÉRICOS
    # ------------------------------------------------------------------ #
    @staticmethod
    def reporte_tabular(
        titulo: str,
        subtitulo: str,
        columnas: List[str],
        filas: List[List[Any]],
    ) -> bytes:
        """
        Genera un PDF con un título, subtítulo y tabla.
        """
        doc, buffer = PDFGenerator._build_doc_buffer()
        styles = PDFGenerator._styles()
        elements = []

        elements.append(Paragraph(titulo, styles["title"]))
        elements.append(
            Paragraph(
                f"{subtitulo}<br/>Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles["small"],
            )
        )
        elements.append(Spacer(1, 12))

        # Transformar filas a texto
        table_data = [columnas]
        for row in filas:
            table_data.append([str(c) for c in row])

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#667eea")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ]
            )
        )

        elements.append(table)
        doc.build(elements)
        return buffer.getvalue()
