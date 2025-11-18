from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BitacoraSesion:
    """
    Representa la entidad BITACORA_SESION.

    Tabla BITACORA_SESION:
      ID_BITACORA, ID_USUARIO, FECHA_LOGIN, FECHA_LOGOUT, IP, DETALLE
    """

    id_bitacora: Optional[int] = None
    id_usuario: int = 0
    fecha_login: Optional[datetime] = None
    fecha_logout: Optional[datetime] = None
    ip: str = ""
    detalle: str = ""

    @classmethod
    def from_dict(cls, row: dict) -> "BitacoraSesion":
        return cls(
            id_bitacora=row.get("ID_BITACORA"),
            id_usuario=row.get("ID_USUARIO"),
            fecha_login=row.get("FECHA_LOGIN"),
            fecha_logout=row.get("FECHA_LOGOUT"),
            ip=row.get("IP") or "",
            detalle=row.get("DETALLE") or "",
        )
