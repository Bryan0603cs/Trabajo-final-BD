from __future__ import annotations

from typing import List, Optional

from config.db_config import get_connection
from model.credito import Credito, Pago


class CreditoDAO:
    """
    CRUD para la tabla CREDITOS + registro de pagos.
    """

    # --------- CREDITOS ---------

    def listar_todos(self) -> List[Credito]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_CREDITO, ID_VENTA, SALDO_TOTAL, SALDO_PENDIENTE,
                       FECHA_VENCIMIENTO, ESTADO
                FROM CREDITOS
                ORDER BY FECHA_VENCIMIENTO
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Credito.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def listar_pendientes(self) -> List[Credito]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_CREDITO, ID_VENTA, SALDO_TOTAL, SALDO_PENDIENTE,
                       FECHA_VENCIMIENTO, ESTADO
                FROM CREDITOS
                WHERE ESTADO = 'VIGENTE' OR ESTADO = 'MORA'
                ORDER BY FECHA_VENCIMIENTO
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Credito.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def obtener_por_id(self, id_credito: int) -> Optional[Credito]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_CREDITO, ID_VENTA, SALDO_TOTAL, SALDO_PENDIENTE,
                       FECHA_VENCIMIENTO, ESTADO
                FROM CREDITOS
                WHERE ID_CREDITO = :id
                """,
                {"id": id_credito},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return Credito.from_dict(dict(zip(cols, row)))
        finally:
            conn.close()

    def crear(self, credito: Credito) -> int:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SEQ_CREDITO.NEXTVAL FROM DUAL")
            new_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO CREDITOS
                    (ID_CREDITO, ID_VENTA, SALDO_TOTAL, SALDO_PENDIENTE,
                     FECHA_VENCIMIENTO, ESTADO)
                VALUES
                    (:id_credito, :id_venta, :saldo_total, :saldo_pendiente,
                     :fecha_vencimiento, :estado)
                """,
                {
                    "id_credito": new_id,
                    "id_venta": credito.id_venta,
                    "saldo_total": credito.saldo_total,
                    "saldo_pendiente": credito.saldo_pendiente,
                    "fecha_vencimiento": credito.fecha_vencimiento,
                    "estado": credito.estado,
                },
            )
            conn.commit()
            credito.id_credito = new_id
            return new_id
        finally:
            conn.close()

    def actualizar(self, credito: Credito) -> None:
        if credito.id_credito is None:
            raise ValueError("El crédito debe tener id_credito para actualizar")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE CREDITOS
                SET SALDO_TOTAL = :saldo_total,
                    SALDO_PENDIENTE = :saldo_pendiente,
                    FECHA_VENCIMIENTO = :fecha_vencimiento,
                    ESTADO = :estado
                WHERE ID_CREDITO = :id_credito
                """,
                {
                    "saldo_total": credito.saldo_total,
                    "saldo_pendiente": credito.saldo_pendiente,
                    "fecha_vencimiento": credito.fecha_vencimiento,
                    "estado": credito.estado,
                    "id_credito": credito.id_credito,
                },
            )
            conn.commit()
        finally:
            conn.close()

    def eliminar(self, id_credito: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            # Primero eliminar pagos asociados
            cur.execute("DELETE FROM PAGOS WHERE ID_CREDITO = :id", {"id": id_credito})
            cur.execute("DELETE FROM CREDITOS WHERE ID_CREDITO = :id", {"id": id_credito})
            conn.commit()
        finally:
            conn.close()

    # --------- PAGOS ---------

    def listar_pagos(self, id_credito: int) -> List[Pago]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_PAGO, ID_CREDITO, FECHA_PAGO, MONTO, SALDO_RESTANTE
                FROM PAGOS
                WHERE ID_CREDITO = :id_credito
                ORDER BY FECHA_PAGO
                """,
                {"id_credito": id_credito},
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Pago.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def registrar_pago(self, pago: Pago) -> int:
        """
        Registra un pago y actualiza el SALDO_PENDIENTE y ESTADO del crédito.
        Asume:
          - pago.id_credito está seteado.
          - pago.monto > 0.
          - saldo_restante se calculará aquí.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            # Obtener crédito actual
            cur.execute(
                """
                SELECT SALDO_PENDIENTE
                FROM CREDITOS
                WHERE ID_CREDITO = :id
                """,
                {"id": pago.id_credito},
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Crédito no encontrado")

            saldo_pendiente_actual = float(row[0] or 0)
            saldo_restante = saldo_pendiente_actual - pago.monto
            if saldo_restante < 0:
                saldo_restante = 0.0

            # Insertar pago
            cur.execute("SELECT SEQ_PAGO.NEXTVAL FROM DUAL")
            new_id_pago = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO PAGOS
                    (ID_PAGO, ID_CREDITO, FECHA_PAGO, MONTO, SALDO_RESTANTE)
                VALUES
                    (:id_pago, :id_credito, SYSDATE, :monto, :saldo_restante)
                """,
                {
                    "id_pago": new_id_pago,
                    "id_credito": pago.id_credito,
                    "monto": pago.monto,
                    "saldo_restante": saldo_restante,
                },
            )

            # Actualizar crédito
            nuevo_estado = "PAGADO" if saldo_restante == 0 else "VIGENTE"
            cur.execute(
                """
                UPDATE CREDITOS
                SET SALDO_PENDIENTE = :saldo_pendiente,
                    ESTADO = :estado
                WHERE ID_CREDITO = :id_credito
                """,
                {
                    "saldo_pendiente": saldo_restante,
                    "estado": nuevo_estado,
                    "id_credito": pago.id_credito,
                },
            )

            conn.commit()
            pago.id_pago = new_id_pago
            pago.saldo_restante = saldo_restante
            return new_id_pago
        finally:
            conn.close()
