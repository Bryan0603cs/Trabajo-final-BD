from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Producto:
    """
    Representa la entidad PRODUCTOS.

    Tabla PRODUCTOS:
      ID_PRODUCTO, NOMBRE, DESCRIPCION,
      PRECIO_COMPRA, PRECIO_VENTA, STOCK,
      ID_CATEGORIA, ID_PROVEEDOR
    """

    id_producto: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    precio_compra: float = 0.0
    precio_venta: float = 0.0
    stock: int = 0
    id_categoria: int = 0
    id_proveedor: Optional[int] = None

    @classmethod
    def from_dict(cls, row: dict) -> "Producto":
        return cls(
            id_producto=row.get("ID_PRODUCTO"),
            nombre=row.get("NOMBRE") or "",
            descripcion=row.get("DESCRIPCION") or "",
            precio_compra=float(row.get("PRECIO_COMPRA") or 0),
            precio_venta=float(row.get("PRECIO_VENTA") or 0),
            stock=int(row.get("STOCK") or 0),
            id_categoria=int(row.get("ID_CATEGORIA") or 0),
            id_proveedor=row.get("ID_PROVEEDOR"),
        )
