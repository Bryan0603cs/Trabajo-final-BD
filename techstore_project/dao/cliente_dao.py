from __future__ import annotations

from typing import List, Optional

from config.db_config import get_connection
from model.cliente import Cliente


class ClienteDAO:
    """CRUD para la tabla CLIENTES."""

    def listar_todos(self) -> List[Cliente]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_CLIENTE, NOMBRE, APELLIDO, DOCUMENTO,
                       TELEFONO, DIRECCION, EMAIL
                FROM CLIENTES
                ORDER BY NOMBRE, APELLIDO
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Cliente.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def obtener_por_id(self, id_cliente: int) -> Optional[Cliente]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_CLIENTE, NOMBRE, APELLIDO, DOCUMENTO,
                       TELEFONO, DIRECCION, EMAIL
                FROM CLIENTES
                WHERE ID_CLIENTE = :id
                """,
                {"id": id_cliente},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return Cliente.from_dict(dict(zip(cols, row)))
        finally:
            conn.close()

    def buscar_por_documento(self, documento: str) -> Optional[Cliente]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_CLIENTE, NOMBRE, APELLIDO, DOCUMENTO,
                       TELEFONO, DIRECCION, EMAIL
                FROM CLIENTES
                WHERE DOCUMENTO = :doc
                """,
                {"doc": documento},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return Cliente.from_dict(dict(zip(cols, row)))
        finally:
            conn.close()

    def crear(self, cliente: Cliente) -> int:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SEQ_CLIENTE.NEXTVAL FROM DUAL")
            new_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO CLIENTES
                    (ID_CLIENTE, NOMBRE, APELLIDO, DOCUMENTO,
                     TELEFONO, DIRECCION, EMAIL)
                VALUES
                    (:id_cliente, :nombre, :apellido, :documento,
                     :telefono, :direccion, :email)
                """,
                {
                    "id_cliente": new_id,
                    "nombre": cliente.nombre,
                    "apellido": cliente.apellido,
                    "documento": cliente.documento,
                    "telefono": cliente.telefono,
                    "direccion": cliente.direccion,
                    "email": cliente.email,
                },
            )
            conn.commit()
            cliente.id_cliente = new_id
            return new_id
        finally:
            conn.close()

    def actualizar(self, cliente: Cliente) -> None:
        if cliente.id_cliente is None:
            raise ValueError("El cliente debe tener id_cliente para actualizar")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE CLIENTES
                SET NOMBRE = :nombre,
                    APELLIDO = :apellido,
                    DOCUMENTO = :documento,
                    TELEFONO = :telefono,
                    DIRECCION = :direccion,
                    EMAIL = :email
                WHERE ID_CLIENTE = :id_cliente
                """,
                {
                    "nombre": cliente.nombre,
                    "apellido": cliente.apellido,
                    "documento": cliente.documento,
                    "telefono": cliente.telefono,
                    "direccion": cliente.direccion,
                    "email": cliente.email,
                    "id_cliente": cliente.id_cliente,
                },
            )
            conn.commit()
        finally:
            conn.close()

    def eliminar(self, id_cliente: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM CLIENTES WHERE ID_CLIENTE = :id", {"id": id_cliente})
            conn.commit()
        finally:
            conn.close()
