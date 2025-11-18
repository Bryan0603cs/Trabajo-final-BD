from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable, List

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def _nuevo_canvas(nombre_archivo: str, titulo: str) -> canvas.Canvas:
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    c.setTitle(titulo)
    return c


def _encabezado(c: canvas.Canvas, titulo: str) -> None:
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, height - 2 * cm, titulo)
    c.setFont("Helvetica", 9)
    c.drawString(2 * cm, height - 2.5 * cm, datetime.now().strftime("%Y-%m-%d %H:%M"))
    c.line(2 * cm, height - 2.7 * cm, width - 2 * cm, height - 2.7 * cm)


def _pie_pagina(c: canvas.Canvas, numero_pagina: int) -> None:
    width, _ = letter
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 2 * cm, 1.5 * cm, f"Página {numero_pagina}")


# ---------------------------------------------------------------------------
# Reporte de ventas por día
# ---------------------------------------------------------------------------

def generar_reporte_ventas_pdf(
    nombre_archivo: str,
    resumen_ventas: Iterable[Dict[str, Any]],
    titulo: str = "Reporte de Ventas por Día",
) -> None:
    """
    Crea un PDF con el resumen de ventas por día.

    Cada fila de resumen_ventas se espera con claves:
      - FECHA
      - NUM_VENTAS
      - TOTAL_VENDIDO
    """
    c = _nuevo_canvas(nombre_archivo, titulo)
    _encabezado(c, titulo)

    width, height = letter
    x_margin = 2 * cm
    y = height - 3.5 * cm
    row_height = 0.6 * cm
    numero_pagina = 1

    # Encabezados de tabla
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_margin, y, "Fecha")
    c.drawString(x_margin + 5 * cm, y, "Nro Ventas")
    c.drawString(x_margin + 9 * cm, y, "Total Vendido")
    y -= row_height
    c.setFont("Helvetica", 10)

    for fila in resumen_ventas:
        if y < 2.5 * cm:  # salto de página
            _pie_pagina(c, numero_pagina)
            c.showPage()
            numero_pagina += 1
            _encabezado(c, titulo)
            y = height - 3.5 * cm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_margin, y, "Fecha")
            c.drawString(x_margin + 5 * cm, y, "Nro Ventas")
            c.drawString(x_margin + 9 * cm, y, "Total Vendido")
            y -= row_height
            c.setFont("Helvetica", 10)

        fecha = fila.get("FECHA")
        if isinstance(fecha, (datetime, date)):
            fecha_str = fecha.strftime("%Y-%m-%d")
        else:
            fecha_str = str(fecha or "")

        num_ventas = int(fila.get("NUM_VENTAS") or 0)
        total = float(fila.get("TOTAL_VENDIDO") or 0.0)

        c.drawString(x_margin, y, fecha_str)
        c.drawString(x_margin + 5 * cm, y, str(num_ventas))
        c.drawRightString(x_margin + 12 * cm, y, f"${total:,.2f}")
        y -= row_height

    _pie_pagina(c, numero_pagina)
    c.save()


# ---------------------------------------------------------------------------
# Reporte de créditos pendientes
# ---------------------------------------------------------------------------

def generar_reporte_creditos_pdf(
    nombre_archivo: str,
    creditos: Iterable[Dict[str, Any]],
    titulo: str = "Reporte de Créditos Pendientes",
) -> None:
    """
    Genera un PDF con la lista de créditos pendientes.

    Cada dict debe tener:
      - ID_CREDITO
      - ID_VENTA
      - CLIENTE
      - SALDO_TOTAL
      - SALDO_PENDIENTE
      - FECHA_VENCIMIENTO
      - ESTADO
    """
    c = _nuevo_canvas(nombre_archivo, titulo)
    _encabezado(c, titulo)

    width, height = letter
    x_margin = 2 * cm
    y = height - 3.5 * cm
    row_height = 0.6 * cm
    numero_pagina = 1

    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_margin, y, "Crédito")
    c.drawString(x_margin + 2.5 * cm, y, "Venta")
    c.drawString(x_margin + 4.8 * cm, y, "Cliente")
    c.drawString(x_margin + 10.0 * cm, y, "Saldo Pendiente")
    c.drawString(x_margin + 14.0 * cm, y, "Vence")
    y -= row_height
    c.setFont("Helvetica", 9)

    for fila in creditos:
        if y < 2.5 * cm:
            _pie_pagina(c, numero_pagina)
            c.showPage()
            numero_pagina += 1
            _encabezado(c, titulo)
            y = height - 3.5 * cm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_margin, y, "Crédito")
            c.drawString(x_margin + 2.5 * cm, y, "Venta")
            c.drawString(x_margin + 4.8 * cm, y, "Cliente")
            c.drawString(x_margin + 10.0 * cm, y, "Saldo Pendiente")
            c.drawString(x_margin + 14.0 * cm, y, "Vence")
            y -= row_height
            c.setFont("Helvetica", 9)

        id_credito = fila.get("ID_CREDITO")
        id_venta = fila.get("ID_VENTA")
        cliente = str(fila.get("CLIENTE") or "")
        saldo_pendiente = float(fila.get("SALDO_PENDIENTE") or 0.0)
        fecha_venc = fila.get("FECHA_VENCIMIENTO")
        if isinstance(fecha_venc, (datetime, date)):
            fecha_venc_str = fecha_venc.strftime("%Y-%m-%d")
        else:
            fecha_venc_str = str(fecha_venc or "")

        c.drawString(x_margin, y, str(id_credito))
        c.drawString(x_margin + 2.5 * cm, y, str(id_venta))
        c.drawString(x_margin + 4.8 * cm, y, cliente[:30])
        c.drawRightString(x_margin + 13.5 * cm, y, f"${saldo_pendiente:,.2f}")
        c.drawString(x_margin + 14.0 * cm, y, fecha_venc_str)
        y -= row_height

    _pie_pagina(c, numero_pagina)
    c.save()


# ---------------------------------------------------------------------------
# Reporte de bitácora de sesiones
# ---------------------------------------------------------------------------

def generar_reporte_bitacora_pdf(
    nombre_archivo: str,
    bitacora: Iterable[Dict[str, Any]],
    titulo: str = "Reporte de Bitácora de Sesiones",
) -> None:
    """
    Genera un PDF con la bitácora de inicio/cierre de sesión.

    Cada dict debe tener:
      - ID_BITACORA
      - USERNAME
      - FECHA_LOGIN
      - FECHA_LOGOUT
      - IP
      - DETALLE
    """
    c = _nuevo_canvas(nombre_archivo, titulo)
    _encabezado(c, titulo)

    width, height = letter
    x_margin = 2 * cm
    y = height - 3.5 * cm
    row_height = 0.5 * cm
    numero_pagina = 1

    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_margin, y, "Usuario")
    c.drawString(x_margin + 4.0 * cm, y, "Login")
    c.drawString(x_margin + 8.0 * cm, y, "Logout")
    c.drawString(x_margin + 12.0 * cm, y, "IP")
    y -= row_height
    c.setFont("Helvetica", 8)

    for fila in bitacora:
        if y < 2.5 * cm:
            _pie_pagina(c, numero_pagina)
            c.showPage()
            numero_pagina += 1
            _encabezado(c, titulo)
            y = height - 3.5 * cm
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_margin, y, "Usuario")
            c.drawString(x_margin + 4.0 * cm, y, "Login")
            c.drawString(x_margin + 8.0 * cm, y, "Logout")
            c.drawString(x_margin + 12.0 * cm, y, "IP")
            y -= row_height
            c.setFont("Helvetica", 8)

        username = str(fila.get("USERNAME") or "")
        fecha_login = fila.get("FECHA_LOGIN")
        fecha_logout = fila.get("FECHA_LOGOUT")
        ip = str(fila.get("IP") or "")

        if isinstance(fecha_login, (datetime, date)):
            login_str = fecha_login.strftime("%Y-%m-%d %H:%M")
        else:
            login_str = str(fecha_login or "")

        if isinstance(fecha_logout, (datetime, date)):
            logout_str = fecha_logout.strftime("%Y-%m-%d %H:%M")
        else:
            logout_str = str(fecha_logout or "")

        c.drawString(x_margin, y, username[:15])
        c.drawString(x_margin + 4.0 * cm, y, login_str)
        c.drawString(x_margin + 8.0 * cm, y, logout_str)
        c.drawString(x_margin + 12.0 * cm, y, ip[:15])
        y -= row_height

    _pie_pagina(c, numero_pagina)
    c.save()
