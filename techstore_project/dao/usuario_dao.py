from __future__ import annotations

from typing import List, Optional

from config.db_config import get_connection
from model.usuario import Usuario


class UsuarioDAO:
    """CRUD para la tabla USUARIOS."""

    def listar_todos(self) -> List[Usuario]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_USUARIO, NOMBRE, APELLIDO, USERNAME, PASSWORD_HASH,
                       ESTADO, FECHA_CREACION, FECHA_MODIFICACION, ID_ROL
                FROM USUARIOS
                ORDER BY NOMBRE, APELLIDO
                """
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [Usuario.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()

    def obtener_por_id(self, id_usuario: int) -> Optional[Usuario]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_USUARIO, NOMBRE, APELLIDO, USERNAME, PASSWORD_HASH,
                       ESTADO, FECHA_CREACION, FECHA_MODIFICACION, ID_ROL
                FROM USUARIOS
                WHERE ID_USUARIO = :id
                """,
                {"id": id_usuario},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return Usuario.from_dict(dict(zip(cols, row)))
        finally:
            conn.close()

    def buscar_por_username(self, username: str) -> Optional[Usuario]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID_USUARIO, NOMBRE, APELLIDO, USERNAME, PASSWORD_HASH,
                       ESTADO, FECHA_CREACION, FECHA_MODIFICACION, ID_ROL
                FROM USUARIOS
                WHERE UPPER(USERNAME) = UPPER(:username)
                """,
                {"username": username},
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return Usuario.from_dict(dict(zip(cols, row)))
        finally:
            conn.close()

    def crear(self, usuario: Usuario) -> int:
        """Inserta un usuario y devuelve el ID generado."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            # Obtenemos el siguiente valor de la secuencia
            cur.execute("SELECT SEQ_USUARIO.NEXTVAL FROM DUAL")
            new_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO USUARIOS
                    (ID_USUARIO, NOMBRE, APELLIDO, USERNAME,
                     PASSWORD_HASH, ESTADO, ID_ROL)
                VALUES
                    (:id_usuario, :nombre, :apellido, :username,
                     :password_hash, :estado, :id_rol)
                """,
                {
                    "id_usuario": new_id,
                    "nombre": usuario.nombre,
                    "apellido": usuario.apellido,
                    "username": usuario.username,
                    "password_hash": usuario.password_hash,
                    "estado": usuario.estado,
                    "id_rol": usuario.id_rol,
                },
            )
            conn.commit()
            usuario.id_usuario = new_id
            return new_id
        finally:
            conn.close()

    def actualizar(self, usuario: Usuario) -> None:
        """Actualiza los datos básicos de un usuario (excepto contraseña)."""
        if usuario.id_usuario is None:
            raise ValueError("El usuario debe tener id_usuario para actualizar")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE USUARIOS
                SET NOMBRE = :nombre,
                    APELLIDO = :apellido,
                    USERNAME = :username,
                    ESTADO = :estado,
                    ID_ROL = :id_rol,
                    FECHA_MODIFICACION = SYSDATE
                WHERE ID_USUARIO = :id_usuario
                """,
                {
                    "nombre": usuario.nombre,
                    "apellido": usuario.apellido,
                    "username": usuario.username,
                    "estado": usuario.estado,
                    "id_rol": usuario.id_rol,
                    "id_usuario": usuario.id_usuario,
                },
            )
            conn.commit()
        finally:
            conn.close()

    def actualizar_password(self, id_usuario: int, nuevo_hash: str) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE USUARIOS
                SET PASSWORD_HASH = :password_hash,
                    FECHA_MODIFICACION = SYSDATE
                WHERE ID_USUARIO = :id_usuario
                """,
                {"password_hash": nuevo_hash, "id_usuario": id_usuario},
            )
            conn.commit()
        finally:
            conn.close()

    def eliminar(self, id_usuario: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM USUARIOS WHERE ID_USUARIO = :id", {"id": id_usuario})
            conn.commit()
        finally:
            conn.close()
