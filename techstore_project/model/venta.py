from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class DetalleVenta:
    """
    Modelo de la tabla DETALLE_VENTAS.

    Tabla DETALLE_VENTAS:
      ID_DETALLE_VENTA, ID_VENTA, ID_PRODUCTO,
      CANTIDAD, PRECIO_UNITARIO, SUBTOTAL
    """

    id_detalle_venta: Optional[int] = None
    id_venta: Optional[int] = None
    id_producto: int = 0
    cantidad: int = 0
    precio_unitario: float = 0.0
    subtotal: float = 0.0

    @classmethod
    def from_dict(cls, row: dict) -> "DetalleVenta":
        return cls(
            id_detalle_venta=row.get("ID_DETALLE_VENTA"),
            id_venta=row.get("ID_VENTA"),
            id_producto=row.get("ID_PRODUCTO"),
            cantidad=int(row.get("CANTIDAD") or 0),
            precio_unitario=float(row.get("PRECIO_UNITARIO") or 0),
            subtotal=float(row.get("SUBTOTAL") or 0),
        )


@dataclass
class Venta:
    """
    Representa la entidad VENTAS.

    Tabla VENTAS:
      ID_VENTA, FECHA, ID_USUARIO, ID_CLIENTE, TOTAL, ES_CREDITO
    """

    id_venta: Optional[int] = None
    fecha: Optional[datetime] = None
    id_usuario: int = 0
    id_cliente: int = 0
    total: float = 0.0
    es_credito: bool = False

    # Detalles asociados (no es columna de BD, es relación 1-N)
    detalles: List[DetalleVenta] = field(default_factory=list)

    @classmethod
    def from_dict(cls, row: dict) -> "Venta":
        return cls(
            id_venta=row.get("ID_VENTA"),
            fecha=row.get("FECHA"),
            id_usuario=row.get("ID_USUARIO"),
            id_cliente=row.get("ID_CLIENTE"),
            total=float(row.get("TOTAL") or 0),
            es_credito=(row.get("ES_CREDITO") == "S"),
        )
