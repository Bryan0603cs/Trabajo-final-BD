from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional, Tuple

from dao.usuario_dao import UsuarioDAO
from dao.bitacora_dao import BitacoraDAO
from model.usuario import Usuario


@dataclass
class ResultadoLogin:
    """
    Resultado de un inicio de sesión exitoso.
    """
    usuario: Usuario
    id_bitacora: int


class AuthService:
    """
    Servicio de autenticación de usuarios.

    Responsabilidades:
      - Validar credenciales de login.
      - Registrar la sesión en BITACORA_SESION.
      - Gestionar cambio de contraseña.
    """

    def __init__(self) -> None:
        self.usuario_dao = UsuarioDAO()
        self.bitacora_dao = BitacoraDAO()

    # ------------------------------------------------------------------ #
    # Utilidades internas
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hash_password(plain_password: str) -> str:
        """
        Devuelve el hash SHA-256 en hexadecimal de la contraseña en texto plano.
        """
        sha = hashlib.sha256()
        sha.update(plain_password.encode("utf-8"))
        return sha.hexdigest()

    # ------------------------------------------------------------------ #
    # Operaciones públicas
    # ------------------------------------------------------------------ #

    def login(
        self,
        username: str,
        password: str,
        ip: str = "",
        detalle: str = "Inicio de sesión",
    ) -> Optional[ResultadoLogin]:
        """
        Intenta autenticar al usuario.

        Retorna:
          - ResultadoLogin(usuario, id_bitacora) si las credenciales son válidas.
          - None si no se encontró usuario o la contraseña es incorrecta.
        """
        usuario = self.usuario_dao.buscar_por_username(username)
        if usuario is None:
            return None
        if usuario.estado != "ACTIVO":
            return None

        hash_ingresado = self._hash_password(password)
        if hash_ingresado != usuario.password_hash:
            return None

        # Registrar login en bitácora
        id_bitacora = self.bitacora_dao.registrar_login(
            id_usuario=usuario.id_usuario,
            ip=ip,
            detalle=detalle,
        )
        return ResultadoLogin(usuario=usuario, id_bitacora=id_bitacora)

    def logout(self, id_bitacora: int) -> None:
        """
        Registra la fecha/hora de logout en la bitácora.
        """
        self.bitacora_dao.registrar_logout(id_bitacora)

    def crear_usuario(
        self,
        nombre: str,
        apellido: str,
        username: str,
        password: str,
        id_rol: int,
        estado: str = "ACTIVO",
    ) -> int:
        """
        Crea un usuario nuevo con contraseña hasheada.
        Devuelve el ID_USUARIO generado.
        """
        usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            username=username,
            password_hash=self._hash_password(password),
            estado=estado,
            id_rol=id_rol,
        )
        return self.usuario_dao.crear(usuario)

    def cambiar_password(self, id_usuario: int, nueva_password: str) -> None:
        """
        Cambia la contraseña de un usuario (almacenando el hash).
        """
        nuevo_hash = self._hash_password(nueva_password)
        self.usuario_dao.actualizar_password(id_usuario, nuevo_hash)
