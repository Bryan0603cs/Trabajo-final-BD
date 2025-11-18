from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Usuario:
    """
    Representa la entidad USUARIOS de la base de datos.

    Tabla USUARIOS:
      ID_USUARIO, NOMBRE, APELLIDO, USERNAME, PASSWORD_HASH,
      ESTADO, FECHA_CREACION, FECHA_MODIFICACION, ID_ROL
    """

    id_usuario: Optional[int] = None
    nombre: str = ""
    apellido: str = ""
    username: str = ""
    password_hash: str = ""
    estado: str = "ACTIVO"
    fecha_creacion: Optional[datetime] = None
    fecha_modificacion: Optional[datetime] = None
    id_rol: int = 0

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    @classmethod
    def from_dict(cls, row: dict) -> "Usuario":
        """Crea un Usuario a partir de un diccionario con claves de columnas Oracle."""
        return cls(
            id_usuario=row.get("ID_USUARIO"),
            nombre=row.get("NOMBRE") or "",
            apellido=row.get("APELLIDO") or "",
            username=row.get("USERNAME") or "",
            password_hash=row.get("PASSWORD_HASH") or "",
            estado=row.get("ESTADO") or "ACTIVO",
            fecha_creacion=row.get("FECHA_CREACION"),
            fecha_modificacion=row.get("FECHA_MODIFICACION"),
            id_rol=row.get("ID_ROL") or 0,
        )
