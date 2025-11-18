from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Categoria:
    """
    Representa la entidad CATEGORIAS.

    Tabla CATEGORIAS:
      ID_CATEGORIA, NOMBRE, DESCRIPCION
    """

    id_categoria: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""

    @classmethod
    def from_dict(cls, row: dict) -> "Categoria":
        return cls(
            id_categoria=row.get("ID_CATEGORIA"),
            nombre=row.get("NOMBRE") or "",
            descripcion=row.get("DESCRIPCION") or "",
        )

