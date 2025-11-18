from __future__ import annotations

from typing import List, Optional

from config.db_config import get_connection
from model.proveedor import Proveedor


class ProveedorDAO:
    """CRUD para la tabla PROVEEDORES."""

    def listar_todos(self) -> List[Proveedor]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_PROVEEDOR, NOMBRE, TELEFONO, EMAIL, DIRECCION
                FROM PROVEEDORES
                ORDER BY NOMBRE
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Proveedor.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def obtener_por_id(self, id_proveedor: int) -> Optional[Proveedor]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_PROVEEDOR, NOMBRE, TELEFONO, EMAIL, DIRECCION
                FROM PROVEEDORES
                WHERE ID_PROVEEDOR = :id
                """,
                {"id": id_proveedor},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return Proveedor.from_dict(dict(zip(cols, row)))
        finally:
            conn.close()

    def crear(self, proveedor: Proveedor) -> int:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SEQ_PROVEEDOR.NEXTVAL FROM DUAL")
            new_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO PROVEEDORES
                    (ID_PROVEEDOR, NOMBRE, TELEFONO, EMAIL, DIRECCION)
                VALUES
                    (:id_proveedor, :nombre, :telefono, :email, :direccion)
                """,
                {
                    "id_proveedor": new_id,
                    "nombre": proveedor.nombre,
                    "telefono": proveedor.telefono,
                    "email": proveedor.email,
                    "direccion": proveedor.direccion,
                },
            )
            conn.commit()
            proveedor.id_proveedor = new_id
            return new_id
        finally:
            conn.close()

    def actualizar(self, proveedor: Proveedor) -> None:
        if proveedor.id_proveedor is None:
            raise ValueError("El proveedor debe tener id_proveedor para actualizar")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE PROVEEDORES
                SET NOMBRE = :nombre,
                    TELEFONO = :telefono,
                    EMAIL = :email,
                    DIRECCION = :direccion
                WHERE ID_PROVEEDOR = :id_proveedor
                """,
                {
                    "nombre": proveedor.nombre,
                    "telefono": proveedor.telefono,
                    "email": proveedor.email,
                    "direccion": proveedor.direccion,
                    "id_proveedor": proveedor.id_proveedor,
                },
            )
            conn.commit()
        finally:
            conn.close()

    def eliminar(self, id_proveedor: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM PROVEEDORES WHERE ID_PROVEEDOR = :id", {"id": id_proveedor})
            conn.commit()
        finally:
            conn.close()
