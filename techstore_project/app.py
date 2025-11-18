from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse

from services.auth_service import AuthService, ResultadoLogin
from services.venta_service import VentaService
from services.reporte_service import ReporteService
from model.usuario import Usuario

# ---------------------------------------------------------------------------
# Config global del servidor
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Roles (IDs en tabla ROLES)
ROLE_ADMIN_ID = 1       # Administrador
ROLE_PARAMETRICO_ID = 2 # Paramétrico
ROLE_ESPORADICO_ID = 3  # Esporádico (si lo creas en BD más adelante)


@dataclass
class Session:
    usuario: Usuario
    id_bitacora: int
    nivel: int  # 1=Admin, 2=Paramétrico, 3=Esporádico


# Sesiones en memoria. En un sistema real usarías otra cosa, pero para
# el proyecto académico es suficiente.
SESSIONS: Dict[str, Session] = {}

# Servicios de negocio (singleton simple)
AUTH_SERVICE = AuthService()
VENTA_SERVICE = VentaService()
REPORTE_SERVICE = ReporteService()


# ---------------------------------------------------------------------------
# Utilidades para plantillas y respuestas
# ---------------------------------------------------------------------------

def render_template(template_name: str, context: Optional[Dict[str, str]] = None) -> str:
    """
    Carga un archivo HTML de templates/ y reemplaza {{placeholders}}.

    Ej:
      context = {"title": "TechStore", "body": "<p>Hola</p>"}
      En la plantilla se usa {{title}} y {{body}}.
    """
    context = context or {}
    template_path = os.path.join(TEMPLATES_DIR, template_name)

    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            content = content.replace(placeholder, value)
        return content

    # Si no existe la plantilla, devolvemos un HTML simple
    title = context.get("title", f"Plantilla {template_name}")
    body = context.get("body", f"<p>Template {template_name} pendiente de implementar.</p>")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    {body}
</body>
</html>
"""



def get_static_file(path: str) -> Optional[bytes]:
    """
    Carga un archivo estático (CSS, JS, imágenes) desde static/.
    """
    full_path = os.path.join(STATIC_DIR, path.lstrip("/"))
    if not os.path.isfile(full_path):
        return None
    with open(full_path, "rb") as f:
        return f.read()


def guess_mime_type(path: str) -> str:
    if path.endswith(".css"):
        return "text/css"
    if path.endswith(".js"):
        return "application/javascript"
    if path.endswith(".png"):
        return "image/png"
    if path.endswith(".jpg") or path.endswith(".jpeg"):
        return "image/jpeg"
    if path.endswith(".ico"):
        return "image/x-icon"
    return "text/plain"


def nivel_from_usuario(usuario: Usuario) -> int:
    """
    Determina el nivel lógico a partir del ID_ROL:
      - 1: Administrador
      - 2: Paramétrico
      - 3: Esporádico
    """
    if usuario.id_rol == ROLE_ADMIN_ID:
        return 1
    if usuario.id_rol == ROLE_PARAMETRICO_ID:
        return 2
    if usuario.id_rol == ROLE_ESPORADICO_ID:
        return 3
    # por defecto lo tratamos como esporádico
    return 3


# ---------------------------------------------------------------------------
# Manejador HTTP
# ---------------------------------------------------------------------------

class TechStoreHandler(BaseHTTPRequestHandler):
    """
    Servidor HTTP sin frameworks para el proyecto TechStore.

    Rutas principales (alineadas con el proyecto):

    - GET  /                → Redirige a /login
    - GET  /login           → Muestra formulario de login
    - POST /login           → Procesa login
    - GET  /logout          → Cierra sesión

    - GET  /menu            → Menú principal
        Secciones visibles:
        - Entidades
        - Transacciones
        - Reportes / Consultas
        - Utilidades
        - Ayudas

    - GET  /entidades       → Página general de Entidades
    - GET  /transacciones   → Página general de Transacciones
    - GET  /reportes        → Página general de Reportes/Consultas
    - GET  /utilidades      → Página general de Utilidades
    - GET  /ayudas          → Página general de Ayudas

    Más adelante se pueden detallar:
      - /entidades/usuarios, /entidades/productos, etc.
      - /transacciones/ventas/nueva, etc.
      - /reportes/ventas, /reportes/creditos, etc.
    """

    # Evitar que http.server imprima cada request en consola
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Si quieres ver los logs, comenta este pass y descomenta el print.
        # print("%s - - [%s] %s" % (self.client_address[0],
        #       self.log_date_time_string(), format % args))
        pass

    # ---------------- Sesiones ---------------- #

    def _get_session_id_from_cookie(self) -> Optional[str]:
        cookie_header = self.headers.get("Cookie")
        if not cookie_header:
            return None
        parts = cookie_header.split(";")
        for part in parts:
            if "=" not in part:
                continue
            name, value = part.strip().split("=", 1)
            if name == "SESSION_ID":
                return value
        return None

    def _get_current_session(self) -> Optional[Session]:
        sid = self._get_session_id_from_cookie()
        if not sid:
            return None
        return SESSIONS.get(sid)

    def _create_session(self, resultado: ResultadoLogin) -> str:
        sid = uuid.uuid4().hex
        nivel = nivel_from_usuario(resultado.usuario)
        SESSIONS[sid] = Session(
            usuario=resultado.usuario,
            id_bitacora=resultado.id_bitacora,
            nivel=nivel,
        )
        return sid

    def _destroy_session(self) -> None:
        sid = self._get_session_id_from_cookie()
        if sid and sid in SESSIONS:
            session = SESSIONS.pop(sid)
            # Registramos logout en la bitácora
            AUTH_SERVICE.logout(session.id_bitacora)

    # -------------- Helpers de respuesta -------------- #

    def _send_html(self, html: str, status: int = 200) -> None:
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    # ----------------- Métodos HTTP ----------------- #

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        # Archivos estáticos (css/js/images)
        if path.startswith("/static/"):
            return self._handle_static(path)

        if path in ("/", "/login"):
            return self._handle_login_page()

        if path == "/logout":
            return self._handle_logout()

        if path == "/menu":
            return self._handle_menu()

        if path == "/entidades":
            return self._handle_entidades()

        if path == "/transacciones":
            return self._handle_transacciones()

        if path == "/reportes":
            return self._handle_reportes()

        if path == "/utilidades":
            return self._handle_utilidades()

        if path == "/ayudas":
            return self._handle_ayudas()

        # Si no coincide con nada:
        self.send_error(404, "Ruta no encontrada")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/login":
            return self._handle_login_submit()

        # Aquí podrás ir añadiendo más POST:
        # - /transacciones/ventas/registrar
        # - /entidades/usuarios/crear
        # etc.
        self.send_error(404, "Ruta POST no encontrada")

    # ----------------- Handlers específicos ----------------- #

    def _handle_static(self, path: str) -> None:
        # path viene como /static/...; recortamos el prefijo.
        rel_path = path[len("/static/") :]
        data = get_static_file(rel_path)
        if data is None:
            self.send_error(404, "Recurso estático no encontrado")
            return

        mime = guess_mime_type(path)
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ---- LOGIN / LOGOUT ---- #

    def _handle_login_page(self) -> None:
        session = self._get_current_session()
        if session:
            # Si ya está logueado, lo mandamos al menú
            return self._redirect("/menu")

        html = render_template(
            "login.html",
            {
                "title": "Login - TechStore",
                # body lo dejamos vacío porque será reemplazado cuando
                # creemos la plantilla; por ahora el placeholder muestra algo.
            },
        )
        self._send_html(html)

    def _handle_login_submit(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(body)

        username = params.get("username", [""])[0].strip()
        password = params.get("password", [""])[0].strip()

        resultado = AUTH_SERVICE.login(username, password, ip=self.client_address[0])

        if resultado is None:
            # Login fallido: volvemos al login con un mensaje simple
            html = render_template(
                "login.html",
                {
                    "title": "Login - TechStore",
                    "body": "<p>Usuario o contraseña incorrectos.</p>",
                },
            )
            return self._send_html(html, status=401)

        # Crear sesión
        sid = self._create_session(resultado)

        # Seteamos cookie y redirigimos a /menu
        self.send_response(302)
        self.send_header("Location", "/menu")
        self.send_header("Set-Cookie", f"SESSION_ID={sid}; HttpOnly; Path=/")
        self.end_headers()

    def _handle_logout(self) -> None:
        self._destroy_session()
        # Borramos cookie (expirándola)
        self.send_response(302)
        self.send_header("Location", "/login")
        self.send_header("Set-Cookie", "SESSION_ID=; Max-Age=0; Path=/")
        self.end_headers()

    # ---- Secciones de menú ---- #

    def _require_session(self) -> Optional[Session]:
        """
        Obtiene la sesión o redirige a /login si no hay usuario autenticado.
        """
        session = self._get_current_session()
        if not session:
            self._redirect("/login")
            return None
        return session

    def _handle_menu(self) -> None:
        session = self._require_session()
        if not session:
            return

        usuario = session.usuario
        nivel = session.nivel

        # Aquí solo mostramos un menú general; luego el HTML real lo
        # montamos en templates/menu_principal.html
        body = f"""
        <p>Bienvenido/a, <strong>{usuario.nombre_completo}</strong> (Nivel {nivel})</p>
        <ul>
            <li><a href="/entidades">Entidades</a></li>
            <li><a href="/transacciones">Transacciones</a></li>
            <li><a href="/reportes">Reportes / Consultas</a></li>
            <li><a href="/utilidades">Utilidades</a></li>
            <li><a href="/ayudas">Ayudas</a></li>
        </ul>
        <p><a href="/logout">Cerrar sesión</a></p>
        """
        html = render_template(
            "menu_principal.html",
            {
                "title": "Menú principal - TechStore",
                "body": body,
            },
        )
        self._send_html(html)

    def _handle_entidades(self) -> None:
        session = self._require_session()
        if not session:
            return

        # Control simple de niveles:
        # - Admin (1): puede ver todo (usuarios, productos, clientes, etc.)
        # - Paramétrico (2): NO puede ver gestión de usuarios ni bitácora
        # - Esporádico (3): en principio no debería gestionar entidades,
        #   pero puede ver listados simples si lo decides así.
        opciones = []

        if session.nivel == 1:
            opciones.append("<li>Gestión de Usuarios (solo Admin)</li>")

        opciones.extend(
            [
                "<li>Gestión de Clientes</li>",
                "<li>Gestión de Categorías</li>",
                "<li>Gestión de Productos</li>",
                "<li>Gestión de Proveedores</li>",
            ]
        )

        body = """
        <h2>Entidades</h2>
        <p>Aquí irán las pantallas de mantenimiento (CRUD) de las tablas principales.</p>
        <ul>
            {opciones}
        </ul>
        <p><a href="/menu">Volver al menú principal</a></p>
        """.format(
            opciones="\n".join(opciones)
        )

        html = render_template(
            "entidades.html",
            {
                "title": "Entidades - TechStore",
                "body": body,
            },
        )
        self._send_html(html)

    def _handle_transacciones(self) -> None:
        session = self._require_session()
        if not session:
            return

        # Aquí la transacción principal es: Ventas (contado / crédito)
        body = """
        <h2>Transacciones (Movimientos)</h2>
        <p>Aquí se manejará el registro de ventas de contado y a crédito.</p>
        <ul>
            <li>Registrar nueva venta de contado</li>
            <li>Registrar nueva venta a crédito</li>
            <li>Consultar ventas realizadas</li>
        </ul>
        <p><em>Más adelante aquí conectaremos los formularios HTML con VentaService.</em></p>
        <p><a href="/menu">Volver al menú principal</a></p>
        """
        html = render_template(
            "ventas.html",
            {
                "title": "Transacciones - TechStore",
                "body": body,
            },
        )
        self._send_html(html)

    def _handle_reportes(self) -> None:
        session = self._require_session()
        if not session:
            return

        # Nivel 3 (esporádico) solo debería acceder a consultas/reportes.
        # Así que este menú está permitido para todos.
        body = """
        <h2>Reportes y Consultas</h2>
        <p>Aquí se implementarán los reportes requeridos por el enunciado:</p>
        <ol>
            <li>Factura de venta del cliente al momento de la compra.</li>
            <li>Total de ventas durante un mes determinado.</li>
            <li>Valor total del IVA a pagar durante un trimestre dado.</li>
            <li>Cantidad de ventas hechas a crédito y de contado en un periodo.</li>
            <li>Inventario de productos por categoría con su costo asociado.</li>
            <li>Clientes que han comprado a crédito y están en mora.</li>
        </ol>
        <p><em>En el código, estos se implementarán usando ReporteService y pdf_generator.</em></p>
        <p><a href="/menu">Volver al menú principal</a></p>
        """
        html = render_template(
            "reportes.html",
            {
                "title": "Reportes y consultas - TechStore",
                "body": body,
            },
        )
        self._send_html(html)

    def _handle_utilidades(self) -> None:
        session = self._require_session()
        if not session:
            return

        # Aquí van mini apps como Calculadora, calendario, etc.,
        # y también la gestión de usuarios y bitácora
        # (solo para el administrador, según el enunciado).
        utilidades = [
            "<li>Calculadora (utilidad)</li>",
            "<li>Calendario (utilidad)</li>",
        ]

        if session.nivel == 1:
            utilidades.extend(
                [
                    "<li>Gestión de usuarios (crear / editar / borrar)</li>",
                    "<li>Bitácora de ingreso y salida de usuarios</li>",
                ]
            )
        else:
            utilidades.append(
                "<li>Gestión de usuarios y bitácora (solo visible para Administrador)</li>"
            )

        body = """
        <h2>Utilidades</h2>
        <ul>
            {contenido}
        </ul>
        <p><a href="/menu">Volver al menú principal</a></p>
        """.format(
            contenido="\n".join(utilidades)
        )

        html = render_template(
            "utilidades.html",
            {
                "title": "Utilidades - TechStore",
                "body": body,
            },
        )
        self._send_html(html)

    def _handle_ayudas(self) -> None:
        session = self._require_session()
        if not session:
            return

        body = """
        <h2>Ayudas</h2>
        <p>Aquí podrás colocar manual de usuario, información de contacto, etc.</p>
        <p>Por ejemplo, una breve guía de cómo usar cada módulo de la aplicación.</p>
        <p><a href="/menu">Volver al menú principal</a></p>
        """
        html = render_template(
            "ayudas.html",
            {
                "title": "Ayudas - TechStore",
                "body": body,
            },
        )
        self._send_html(html)


# ---------------------------------------------------------------------------
# Función para arrancar el servidor
# ---------------------------------------------------------------------------

def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """
    Arranca el servidor HTTP en el host/puerto indicados.
    """
    server_address = (host, port)
    httpd = HTTPServer(server_address, TechStoreHandler)
    try:
        print(f"Servidor HTTP escuchando en http://{host}:{port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
    finally:
        httpd.server_close()
        print("Servidor detenido.")
