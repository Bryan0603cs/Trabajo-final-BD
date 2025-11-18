from __future__ import annotations

from typing import List, Optional

from config.db_config import get_connection
from model.venta import Venta, DetalleVenta


class VentaDAO:
    """
    CRUD para la tabla VENTAS y manejo de DETALLE_VENTAS.
    """

    # --------- VENTAS ---------

    def listar_todas(self) -> List[Venta]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_VENTA, FECHA, ID_USUARIO, ID_CLIENTE, TOTAL, ES_CREDITO
                FROM VENTAS
                ORDER BY FECHA DESC
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            ventas = [Venta.from_dict(dict(zip(cols, r))) for r in rows]

            # Cargar detalles de cada venta
            for venta in ventas:
                venta.detalles = self.obtener_detalles(venta.id_venta)
            return ventas
        finally:
            conn.close()

    def obtener_por_id(self, id_venta: int) -> Optional[Venta]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_VENTA, FECHA, ID_USUARIO, ID_CLIENTE, TOTAL, ES_CREDITO
                FROM VENTAS
                WHERE ID_VENTA = :id
                """,
                {"id": id_venta},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            venta = Venta.from_dict(dict(zip(cols, row)))
            venta.detalles = self.obtener_detalles(venta.id_venta)
            return venta
        finally:
            conn.close()

    def crear(self, venta: Venta) -> int:
        """
        Inserta una venta con sus detalles.
        - Usa SEQ_VENTA y SEQ_DETALLE_VENTA.
        - Asume que venta.detalles ya viene con id_producto, cantidad y precio_unitario.
        - Calcula total si es necesario.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            # Si el total viene en 0, lo calculamos a partir de detalles
            if venta.total == 0 and venta.detalles:
                venta.total = sum(d.cantidad * d.precio_unitario for d in venta.detalles)

            # Obtener ID de la venta
            cur.execute("SELECT SEQ_VENTA.NEXTVAL FROM DUAL")
            new_id_venta = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO VENTAS
                    (ID_VENTA, FECHA, ID_USUARIO, ID_CLIENTE, TOTAL, ES_CREDITO)
                VALUES
                    (:id_venta, SYSDATE, :id_usuario, :id_cliente, :total, :es_credito)
                """,
                {
                    "id_venta": new_id_venta,
                    "id_usuario": venta.id_usuario,
                    "id_cliente": venta.id_cliente,
                    "total": venta.total,
                    "es_credito": "S" if venta.es_credito else "N",
                },
            )

            # Insertar detalles
            for det in venta.detalles:
                self._insertar_detalle(cur, new_id_venta, det)

            conn.commit()
            venta.id_venta = new_id_venta
            return new_id_venta
        finally:
            conn.close()

    def eliminar(self, id_venta: int) -> None:
        """
        Elimina los detalles y luego la venta.
        (En un proyecto real podrías preferir un campo estado en vez de borrado duro).
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM DETALLE_VENTAS WHERE ID_VENTA = :id", {"id": id_venta})
            cur.execute("DELETE FROM VENTAS WHERE ID_VENTA = :id", {"id": id_venta})
            conn.commit()
        finally:
            conn.close()

    # --------- DETALLE_VENTAS ---------

    def obtener_detalles(self, id_venta: int | None) -> List[DetalleVenta]:
        if id_venta is None:
            return []

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_DETALLE_VENTA, ID_VENTA, ID_PRODUCTO,
                       CANTIDAD, PRECIO_UNITARIO, SUBTOTAL
                FROM DETALLE_VENTAS
                WHERE ID_VENTA = :id_venta
                """,
                {"id_venta": id_venta},
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [DetalleVenta.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def _insertar_detalle(self, cur, id_venta: int, detalle: DetalleVenta) -> None:
        """Método interno para insertar un detalle de venta usando un cursor existente."""
        if detalle.subtotal == 0:
            detalle.subtotal = detalle.cantidad * detalle.precio_unitario

        cur.execute("SELECT SEQ_DETALLE_VENTA.NEXTVAL FROM DUAL")
        new_id_det = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO DETALLE_VENTAS
                (ID_DETALLE_VENTA, ID_VENTA, ID_PRODUCTO,
                 CANTIDAD, PRECIO_UNITARIO, SUBTOTAL)
            VALUES
                (:id_detalle, :id_venta, :id_producto,
                 :cantidad, :precio_unitario, :subtotal)
            """,
            {
                "id_detalle": new_id_det,
                "id_venta": id_venta,
                "id_producto": detalle.id_producto,
                "cantidad": detalle.cantidad,
                "precio_unitario": detalle.precio_unitario,
                "subtotal": detalle.subtotal,
            },
        )
        detalle.id_detalle_venta = new_id_det
        detalle.id_venta = id_venta
