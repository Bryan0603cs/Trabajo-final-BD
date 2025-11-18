from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Credito:
    """
    Representa la entidad CREDITOS.

    Tabla CREDITOS:
      ID_CREDITO, ID_VENTA, SALDO_TOTAL, SALDO_PENDIENTE,
      FECHA_VENCIMIENTO, ESTADO
    """

    id_credito: Optional[int] = None
    id_venta: int = 0
    saldo_total: float = 0.0
    saldo_pendiente: float = 0.0
    fecha_vencimiento: Optional[date] = None
    estado: str = "VIGENTE"

    @classmethod
    def from_dict(cls, row: dict) -> "Credito":
        return cls(
            id_credito=row.get("ID_CREDITO"),
            id_venta=row.get("ID_VENTA"),
            saldo_total=float(row.get("SALDO_TOTAL") or 0),
            saldo_pendiente=float(row.get("SALDO_PENDIENTE") or 0),
            fecha_vencimiento=row.get("FECHA_VENCIMIENTO"),
            estado=row.get("ESTADO") or "VIGENTE",
        )


@dataclass
class Pago:
    """
    Modelo de la tabla PAGOS.

    Tabla PAGOS:
      ID_PAGO, ID_CREDITO, FECHA_PAGO, MONTO, SALDO_RESTANTE
    """

    id_pago: Optional[int] = None
    id_credito: int = 0
    fecha_pago: Optional[date] = None
    monto: float = 0.0
    saldo_restante: float = 0.0

    @classmethod
    def from_dict(cls, row: dict) -> "Pago":
        return cls(
            id_pago=row.get("ID_PAGO"),
            id_credito=row.get("ID_CREDITO"),
            fecha_pago=row.get("FECHA_PAGO"),
            monto=float(row.get("MONTO") or 0),
            saldo_restante=float(row.get("SALDO_RESTANTE") or 0),
        )
