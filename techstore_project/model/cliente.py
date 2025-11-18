from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Cliente:
    """
    Representa la entidad CLIENTES.

    Tabla CLIENTES:
      ID_CLIENTE, NOMBRE, APELLIDO, DOCUMENTO, TELEFONO, DIRECCION, EMAIL
    """

    id_cliente: Optional[int] = None
    nombre: str = ""
    apellido: str = ""
    documento: str = ""
    telefono: str = ""
    direccion: str = ""
    email: str = ""

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    @classmethod
    def from_dict(cls, row: dict) -> "Cliente":
        return cls(
            id_cliente=row.get("ID_CLIENTE"),
            nombre=row.get("NOMBRE") or "",
            apellido=row.get("APELLIDO") or "",
            documento=row.get("DOCUMENTO") or "",
            telefono=row.get("TELEFONO") or "",
            direccion=row.get("DIRECCION") or "",
            email=row.get("EMAIL") or "",
        )
