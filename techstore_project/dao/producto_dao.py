from __future__ import annotations

from typing import List, Optional

from config.db_config import get_connection
from model.producto import Producto


class ProductoDAO:
    """CRUD para la tabla PRODUCTOS y consultas asociadas."""

    def listar_todos(self) -> List[Producto]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_PRODUCTO, NOMBRE, DESCRIPCION,
                       PRECIO_COMPRA, PRECIO_VENTA, STOCK,
                       ID_CATEGORIA, ID_PROVEEDOR
                FROM PRODUCTOS
                ORDER BY NOMBRE
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Producto.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def listar_disponibles(self) -> List[Producto]:
        """Lista productos con stock > 0."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_PRODUCTO, NOMBRE, DESCRIPCION,
                       PRECIO_COMPRA, PRECIO_VENTA, STOCK,
                       ID_CATEGORIA, ID_PROVEEDOR
                FROM PRODUCTOS
                WHERE STOCK > 0
                ORDER BY NOMBRE
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Producto.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def obtener_por_id(self, id_producto: int) -> Optional[Producto]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_PRODUCTO, NOMBRE, DESCRIPCION,
                       PRECIO_COMPRA, PRECIO_VENTA, STOCK,
                       ID_CATEGORIA, ID_PROVEEDOR
                FROM PRODUCTOS
                WHERE ID_PRODUCTO = :id
                """,
                {"id": id_producto},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return Producto.from_dict(dict(zip(cols, row)))
        finally:
            conn.close()

    def crear(self, producto: Producto) -> int:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SEQ_PRODUCTO.NEXTVAL FROM DUAL")
            new_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO PRODUCTOS
                    (ID_PRODUCTO, NOMBRE, DESCRIPCION,
                     PRECIO_COMPRA, PRECIO_VENTA, STOCK,
                     ID_CATEGORIA, ID_PROVEEDOR)
                VALUES
                    (:id_producto, :nombre, :descripcion,
                     :precio_compra, :precio_venta, :stock,
                     :id_categoria, :id_proveedor)
                """,
                {
                    "id_producto": new_id,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "precio_compra": producto.precio_compra,
                    "precio_venta": producto.precio_venta,
                    "stock": producto.stock,
                    "id_categoria": producto.id_categoria,
                    "id_proveedor": producto.id_proveedor,
                },
            )
            conn.commit()
            producto.id_producto = new_id
            return new_id
        finally:
            conn.close()

    def actualizar(self, producto: Producto) -> None:
        if producto.id_producto is None:
            raise ValueError("El producto debe tener id_producto para actualizar")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE PRODUCTOS
                SET NOMBRE = :nombre,
                    DESCRIPCION = :descripcion,
                    PRECIO_COMPRA = :precio_compra,
                    PRECIO_VENTA = :precio_venta,
                    STOCK = :stock,
                    ID_CATEGORIA = :id_categoria,
                    ID_PROVEEDOR = :id_proveedor
                WHERE ID_PRODUCTO = :id_producto
                """,
                {
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "precio_compra": producto.precio_compra,
                    "precio_venta": producto.precio_venta,
                    "stock": producto.stock,
                    "id_categoria": producto.id_categoria,
                    "id_proveedor": producto.id_proveedor,
                    "id_producto": producto.id_producto,
                },
            )
            conn.commit()
        finally:
            conn.close()

    def actualizar_stock(self, id_producto: int, nuevo_stock: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE PRODUCTOS
                SET STOCK = :stock
                WHERE ID_PRODUCTO = :id_producto
                """,
                {"stock": nuevo_stock, "id_producto": id_producto},
            )
            conn.commit()
        finally:
            conn.close()

    def eliminar(self, id_producto: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM PRODUCTOS WHERE ID_PRODUCTO = :id", {"id": id_producto})
            conn.commit()
        finally:
            conn.close()
