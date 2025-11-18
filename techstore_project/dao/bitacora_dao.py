from __future__ import annotations

from typing import List

from config.db_config import get_connection
from model.bitacora import BitacoraSesion


class BitacoraDAO:
    """
    DAO para la tabla BITACORA_SESION.
    Registra logins/logouts y permite consultar el historial.
    """

    def registrar_login(self, id_usuario: int, ip: str = "", detalle: str = "") -> int:
        """
        Inserta un registro de login (FECHA_LOGIN = SYSDATE, FECHA_LOGOUT NULL).
        Devuelve el ID_BITACORA generado.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SEQ_BITACORA.NEXTVAL FROM DUAL")
            new_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO BITACORA_SESION
                    (ID_BITACORA, ID_USUARIO, FECHA_LOGIN, IP, DETALLE)
                VALUES
                    (:id_bitacora, :id_usuario, SYSDATE, :ip, :detalle)
                """,
                {
                    "id_bitacora": new_id,
                    "id_usuario": id_usuario,
                    "ip": ip,
                    "detalle": detalle,
                },
            )
            conn.commit()
            return new_id
        finally:
            conn.close()

    def registrar_logout(self, id_bitacora: int) -> None:
        """
        Actualiza el registro indicado poniendo FECHA_LOGOUT = SYSDATE.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE BITACORA_SESION
                SET FECHA_LOGOUT = SYSDATE
                WHERE ID_BITACORA = :id
                """,
                {"id": id_bitacora},
            )
            conn.commit()
        finally:
            conn.close()

    def listar_ultimos(self, limite: int = 50) -> List[BitacoraSesion]:
        """
        Lista los últimos `limite` eventos de bitácora, ordenados por FECHA_LOGIN desc.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT ID_BITACORA, ID_USUARIO, FECHA_LOGIN, FECHA_LOGOUT, IP, DETALLE
                FROM (
                    SELECT ID_BITACORA, ID_USUARIO, FECHA_LOGIN, FECHA_LOGOUT, IP, DETALLE
                    FROM BITACORA_SESION
                    ORDER BY FECHA_LOGIN DESC
                )
                WHERE ROWNUM <= :limite
                """,
                {"limite": limite},
            )
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            return [BitacoraSesion.from_dict(dict(zip(cols, r))) for r in rows]
        finally:
            conn.close()
