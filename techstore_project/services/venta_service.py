from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional, Tuple

from dao.producto_dao import ProductoDAO
from dao.venta_dao import VentaDAO
from dao.credito_dao import CreditoDAO
from model.credito import Credito
from model.venta import Venta, DetalleVenta


class VentaService:
    """
    Servicio de negocio para el módulo de ventas.

    Responsabilidades:
      - Registrar ventas de contado y a crédito.
      - Validar stock de productos.
      - Actualizar stock después de la venta.
      - Crear el registro de crédito cuando aplica.
    """

    def __init__(self) -> None:
        self.producto_dao = ProductoDAO()
        self.venta_dao = VentaDAO()
        self.credito_dao = CreditoDAO()

    # ------------------------------------------------------------------ #
    # Helpers internos
    # ------------------------------------------------------------------ #

    def _validar_y_cargar_productos(
        self,
        items: Iterable[dict],
    ) -> List[Tuple[dict, object]]:
        """
        Valida que cada producto exista y tenga stock suficiente.

        items: iterable de dict con al menos:
            { "id_producto": int, "cantidad": int }

        Retorna una lista de tuplas (item, producto_model).
        Lanza ValueError si algo falla.
        """
        resultado: List[Tuple[dict, object]] = []

        for item in items:
            id_producto = int(item["id_producto"])
            cantidad = int(item["cantidad"])
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida para producto {id_producto}")

            producto = self.producto_dao.obtener_por_id(id_producto)
            if producto is None:
                raise ValueError(f"Producto {id_producto} no existe")
            if producto.stock < cantidad:
                raise ValueError(
                    f"Stock insuficiente para producto {producto.nombre} "
                    f"(stock={producto.stock}, solicitado={cantidad})"
                )
            resultado.append((item, producto))

        return resultado

    def _construir_detalles(
        self,
        productos_validados: List[Tuple[dict, object]],
    ) -> List[DetalleVenta]:
        """
        Construye la lista de DetalleVenta a partir de los productos validados.
        Usa PRECIO_VENTA como precio_unitario.
        """
        detalles: List[DetalleVenta] = []
        for item, producto in productos_validados:
            cantidad = int(item["cantidad"])
            precio_unitario = float(producto.precio_venta)
            detalles.append(
                DetalleVenta(
                    id_producto=producto.id_producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=cantidad * precio_unitario,
                )
            )
        return detalles

    def _actualizar_stock_despues_de_venta(
        self,
        productos_validados: List[Tuple[dict, object]],
    ) -> None:
        """
        Resta del stock la cantidad vendida por producto.
        """
        for item, producto in productos_validados:
            cantidad = int(item["cantidad"])
            nuevo_stock = int(producto.stock) - cantidad
            self.producto_dao.actualizar_stock(producto.id_producto, nuevo_stock)

    # ------------------------------------------------------------------ #
    # Operaciones públicas
    # ------------------------------------------------------------------ #

    def registrar_venta_contado(
        self,
        id_usuario: int,
        id_cliente: int,
        items: Iterable[dict],
    ) -> int:
        """
        Registra una venta de contado.

        items: iterable de dicts:
            { "id_producto": int, "cantidad": int }

        Devuelve: ID_VENTA generado.
        """
        productos_validados = self._validar_y_cargar_productos(items)
        detalles = self._construir_detalles(productos_validados)

        venta = Venta(
            id_usuario=id_usuario,
            id_cliente=id_cliente,
            es_credito=False,
            detalles=detalles,
        )

        id_venta = self.venta_dao.crear(venta)
        self._actualizar_stock_despues_de_venta(productos_validados)
        return id_venta

    def registrar_venta_credito(
        self,
        id_usuario: int,
        id_cliente: int,
        items: Iterable[dict],
        fecha_vencimiento: date,
    ) -> Tuple[int, int]:
        """
        Registra una venta a crédito y su correspondiente crédito.

        Retorna: (ID_VENTA, ID_CREDITO)
        """
        productos_validados = self._validar_y_cargar_productos(items)
        detalles = self._construir_detalles(productos_validados)

        venta = Venta(
            id_usuario=id_usuario,
            id_cliente=id_cliente,
            es_credito=True,
            detalles=detalles,
        )

        id_venta = self.venta_dao.crear(venta)
        self._actualizar_stock_despues_de_venta(productos_validados)

        # Crear crédito asociado
        credito = Credito(
            id_venta=id_venta,
            saldo_total=venta.total,
            saldo_pendiente=venta.total,
            fecha_vencimiento=fecha_vencimiento,
            estado="VIGENTE",
        )
        id_credito = self.credito_dao.crear(credito)

        return id_venta, id_credito

    def obtener_venta_detallada(self, id_venta: int) -> Optional[Venta]:
        """
        Devuelve la venta con sus detalles cargados.
        """
        return self.venta_dao.obtener_por_id(id_venta)

    def listar_ventas(self) -> List[Venta]:
        """
        Devuelve todas las ventas con sus detalles.
        (Para reportes/consultas generales.)
        """
        return self.venta_dao.listar_todas()
