from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Proveedor:
    """
    Representa la entidad PROVEEDORES.

    Tabla PROVEEDORES:
      ID_PROVEEDOR, NOMBRE, TELEFONO, EMAIL, DIRECCION
    """

    id_proveedor: Optional[int] = None
    nombre: str = ""
    telefono: str = ""
    email: str = ""
    direccion: str = ""

    @classmethod
    def from_dict(cls, row: dict) -> "Proveedor":
        return cls(
            id_proveedor=row.get("ID_PROVEEDOR"),
            nombre=row.get("NOMBRE") or "",
            telefono=row.get("TELEFONO") or "",
            email=row.get("EMAIL") or "",
            direccion=row.get("DIRECCION") or "",
        )
