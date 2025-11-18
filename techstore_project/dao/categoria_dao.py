from __future__ import annotations

from typing import List, Optional

from config.db_config import get_connection
from model.categoria import Categoria


class CategoriaDAO:
    """CRUD para la tabla CATEGORIAS."""

    def listar_todas(self) -> List[Categoria]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_CATEGORIA, NOMBRE, DESCRIPCION
                FROM CATEGORIAS
                ORDER BY NOMBRE
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Categoria.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def obtener_por_id(self, id_categoria: int) -> Optional[Categoria]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_CATEGORIA, NOMBRE, DESCRIPCION
                FROM CATEGORIAS
                WHERE ID_CATEGORIA = :id
                """,
                {"id": id_categoria},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return Categoria.from_dict(dict(zip(cols, row)))
        finally:
            conn.close()

    def crear(self, categoria: Categoria) -> int:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SEQ_CATEGORIA.NEXTVAL FROM DUAL")
            new_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO CATEGORIAS (ID_CATEGORIA, NOMBRE, DESCRIPCION)
                VALUES (:id_categoria, :nombre, :descripcion)
                """,
                {
                    "id_categoria": new_id,
                    "nombre": categoria.nombre,
                    "descripcion": categoria.descripcion,
                },
            )
            conn.commit()
            categoria.id_categoria = new_id
            return new_id
        finally:
            conn.close()

    def actualizar(self, categoria: Categoria) -> None:
        if categoria.id_categoria is None:
            raise ValueError("La categoría debe tener id_categoria para actualizar")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE CATEGORIAS
                SET NOMBRE = :nombre,
                    DESCRIPCION = :descripcion
                WHERE ID_CATEGORIA = :id_categoria
                """,
                {
                    "nombre": categoria.nombre,
                    "descripcion": categoria.descripcion,
                    "id_categoria": categoria.id_categoria,
                },
            )
            conn.commit()
        finally:
            conn.close()

    def eliminar(self, id_categoria: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM CATEGORIAS WHERE ID_CATEGORIA = :id", {"id": id_categoria})
            conn.commit()
        finally:
            conn.close()
