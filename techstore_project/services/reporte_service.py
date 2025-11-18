from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from config.db_config import get_connection


class ReporteService:
    """
    Servicio para obtención de datos de reportes.

    Se apoya directamente en SQL porque los reportes suelen requerir
    agregaciones (SUM, COUNT, GROUP BY) y joins específicos.
    """

    # ------------------------------------------------------------------ #
    # Ventas
    # ------------------------------------------------------------------ #

    def resumen_ventas_por_dia(
        self,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retorna una lista de dicts con:
          - FECHA (date)
          - NUM_VENTAS (int)
          - TOTAL_VENDIDO (float)
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            condiciones = []
            params: Dict[str, Any] = {}

            if fecha_inicio is not None:
                condiciones.append("TRUNC(FECHA) >= :fi")
                params["fi"] = fecha_inicio
            if fecha_fin is not None:
                condiciones.append("TRUNC(FECHA) <= :ff")
                params["ff"] = fecha_fin

            where_clause = ""
            if condiciones:
                where_clause = "WHERE " + " AND ".join(condiciones)

            sql = f"""
                SELECT
                    TRUNC(FECHA) AS FECHA,
                    COUNT(*)      AS NUM_VENTAS,
                    SUM(TOTAL)    AS TOTAL_VENDIDO
                FROM VENTAS
                {where_clause}
                GROUP BY TRUNC(FECHA)
                ORDER BY FECHA
            """

            cur.execute(sql, params)
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Créditos pendientes
    # ------------------------------------------------------------------ #

    def creditos_pendientes(self) -> List[Dict[str, Any]]:
        """
        Retorna créditos en estado VIGENTE o MORA con datos del cliente.
        Campos:
          - ID_CREDITO
          - ID_VENTA
          - CLIENTE
          - SALDO_TOTAL
          - SALDO_PENDIENTE
          - FECHA_VENCIMIENTO
          - ESTADO
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    c.ID_CREDITO,
                    c.ID_VENTA,
                    cli.NOMBRE || ' ' || cli.APELLIDO AS CLIENTE,
                    c.SALDO_TOTAL,
                    c.SALDO_PENDIENTE,
                    c.FECHA_VENCIMIENTO,
                    c.ESTADO
                FROM CREDITOS c
                JOIN VENTAS v ON v.ID_VENTA = c.ID_VENTA
                JOIN CLIENTES cli ON cli.ID_CLIENTE = v.ID_CLIENTE
                WHERE c.ESTADO IN ('VIGENTE', 'MORA')
                ORDER BY c.FECHA_VENCIMIENTO
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Bitácora de sesiones
    # ------------------------------------------------------------------ #

    def bitacora_sesiones(self, limite: int = 50) -> List[Dict[str, Any]]:
        """
        Retorna los últimos N registros de bitácora con el username.
        Campos:
          - ID_BITACORA
          - USERNAME
          - FECHA_LOGIN
          - FECHA_LOGOUT
          - IP
          - DETALLE
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT *
                FROM (
                    SELECT
                        b.ID_BITACORA,
                        u.USERNAME,
                        b.FECHA_LOGIN,
                        b.FECHA_LOGOUT,
                        b.IP,
                        b.DETALLE
                    FROM BITACORA_SESION b
                    JOIN USUARIOS u ON u.ID_USUARIO = b.ID_USUARIO
                    ORDER BY b.FECHA_LOGIN DESC
                )
                WHERE ROWNUM <= :limite
                """,
                {"limite": limite},
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        finally:
            conn.close()
