from __future__ import annotations

import json
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


# Sesiones en memoria
SESSIONS: Dict[str, Session] = {}

# Servicios de negocio (singleton simple)
AUTH_SERVICE = AuthService()
VENTA_SERVICE = VentaService()
REPORTE_SERVICE = ReporteService()


# ---------------------------------------------------------------------------
# Utilidades para plantillas y recursos estáticos
# ---------------------------------------------------------------------------

def render_template(template_name: str, context: Optional[Dict[str, str]] = None) -> str:
    """
    Carga un archivo HTML de templates/ y reemplaza {{placeholders}}.
    """
    context = context or {}
    template_path = os.path.join(TEMPLATES_DIR, template_name)

    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            content = content.replace(placeholder, str(value))
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
    return 3


# ---------------------------------------------------------------------------
# Manejador HTTP
# ---------------------------------------------------------------------------

class TechStoreHandler(BaseHTTPRequestHandler):
    auth_service = AuthService()
    reporte_service = ReporteService()

    """
    Servidor HTTP sin frameworks para el proyecto TechStore.
    """

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Comenta el pass y descomenta el print si quieres ver logs.
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

    def _send_json(
        self,
        obj: Dict[str, object],
        status: int = 200,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _send_pdf(self, pdf_bytes: bytes, filename: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'inline; filename="{filename}"')
        self.send_header("Content-Length", str(len(pdf_bytes)))
        self.end_headers()
        self.wfile.write(pdf_bytes)

    def _redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    # ----------------- Métodos HTTP ----------------- #

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Archivos estáticos (css/js/images)
        if path.startswith("/static/"):
            return self._handle_static(path)

        # Login (incluye alias /login.html)
        if path in ("/", "/login", "/login.html"):
            return self._handle_login_page()

        if path == "/logout":
            return self._handle_logout()

        # Menú principal (alias /menu_principal.html)
        if path in ("/menu", "/menu_principal.html"):
            return self._handle_menu()

        # Páginas principales
        if path in ("/entidades", "/entidades.html"):
            return self._handle_entidades()

        if path in ("/transacciones", "/transacciones.html", "/ventas", "/ventas.html"):
            return self._handle_transacciones()

        if path in ("/reportes", "/reportes.html"):
            return self._handle_reportes()

        if path in ("/utilidades", "/utilidades.html"):
            return self._handle_utilidades()

        if path in ("/ayudas", "/ayudas.html"):
            return self._handle_ayudas()

        # Páginas detalladas adicionales
        if path in ("/usuarios", "/usuarios.html"):
            return self._handle_usuarios()

        if path in ("/clientes", "/clientes.html"):
            return self._handle_clientes()

        if path in ("/productos", "/productos.html"):
            return self._handle_productos()

        if path in ("/categorias", "/categorias.html"):
            return self._handle_categorias()

        if path in ("/creditos", "/creditos.html"):
            return self._handle_creditos()

        if path in ("/consultas", "/consultas.html"):
            return self._handle_consultas()

        if path in ("/bitacora", "/bitacora.html"):
            return self._handle_bitacora()

        if path in ("/registro", "/registro.html"):
            return self._handle_registro()

        # Endpoints PDF de reportes
        if path == "/reportes/factura":
            return self._handle_reporte_factura(query)

        if path == "/reportes/ventas-mes":
            return self._handle_reporte_ventas_mes(query)

        if path == "/reportes/iva-trimestre":
            return self._handle_reporte_iva_trimestre(query)

        if path == "/reportes/ventas-tipo":
            return self._handle_reporte_ventas_tipo(query)

        if path == "/reportes/inventario-categoria":
            return self._handle_reporte_inventario_categoria()

        if path == "/reportes/clientes-mora":
            return self._handle_reporte_clientes_mora()

        # Si no coincide con nada:
        self.send_error(404, "Ruta no encontrada")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        # Login clásico (form POST /login)
        if path == "/login":
            return self._handle_login_submit()

        # Login nuevo con fetch('/api/login') desde login.html
        if path == "/api/login":
            return self._handle_api_login()

        # Aquí podrás ir añadiendo más POST:
        # - /transacciones/ventas/registrar
        # - /entidades/usuarios/crear
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

    def _handle_api_login(self) -> None:
        """
        Endpoint para el login por fetch('/api/login') que usa tu login.html moderno.
        Espera JSON: { "correo": "...", "contrasena": "..." }
        y responde JSON: { "success": true/false, "message": "...", "usuario": {...} }
        """
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return self._send_json(
                {"success": False, "message": "JSON inválido"},
                status=400,
            )

        username = (data.get("correo") or data.get("username") or "").strip()
        password = (data.get("contrasena") or data.get("password") or "").strip()

        if not username or not password:
            return self._send_json(
                {"success": False, "message": "Usuario y contraseña son obligatorios"},
                status=400,
            )

        resultado = AUTH_SERVICE.login(username, password, ip=self.client_address[0])

        if resultado is None:
            return self._send_json(
                {"success": False, "message": "Usuario o contraseña incorrectos"},
                status=401,
            )

        # Crear sesión y cookie
        sid = self._create_session(resultado)
        usuario = resultado.usuario

        public_user = {
            "id_usuario": getattr(usuario, "id_usuario", None),
            "username": getattr(usuario, "username", None),
            "nombre": getattr(usuario, "nombre", None),
            "apellido": getattr(usuario, "apellido", None),
            "rol": getattr(usuario, "id_rol", None),
        }

        headers = {"Set-Cookie": f"SESSION_ID={sid}; HttpOnly; Path=/"}
        return self._send_json(
            {"success": True, "usuario": public_user},
            status=200,
            extra_headers=headers,
        )

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

    def _render_simple_page(self, template: str, title: str, extra_ctx: Optional[Dict[str, str]] = None) -> None:
        session = self._require_session()
        if not session:
            return
        ctx = {"title": title}
        if extra_ctx:
            ctx.update(extra_ctx)
        html = render_template(template, ctx)
        self._send_html(html)

    def _handle_menu(self) -> None:
        session = self._require_session()
        if not session:
            return

        usuario = session.usuario
        nombre = getattr(usuario, "nombre_completo", None) or getattr(usuario, "nombre", "")
        self._render_simple_page(
            "menu_principal.html",
            "Menú principal - TechStore",
            {"usuario_nombre": nombre},
        )

    def _handle_entidades(self) -> None:
        self._render_simple_page("entidades.html", "Entidades - TechStore")

    def _handle_transacciones(self) -> None:
        # La plantilla ventas.html describe el módulo de ventas
        self._render_simple_page("ventas.html", "Transacciones / Ventas - TechStore")

    def _handle_reportes(self) -> None:
        self._render_simple_page("reportes.html", "Reportes y consultas - TechStore")

    def _handle_utilidades(self) -> None:
        self._render_simple_page("utilidades.html", "Utilidades - TechStore")

    def _handle_ayudas(self) -> None:
        self._render_simple_page("ayudas.html", "Ayudas - TechStore")

    def _handle_usuarios(self) -> None:
        self._render_simple_page("usuarios.html", "Usuarios y roles - TechStore")

    def _handle_clientes(self) -> None:
        self._render_simple_page("clientes.html", "Clientes - TechStore")

    def _handle_productos(self) -> None:
        self._render_simple_page("productos.html", "Productos - TechStore")

    def _handle_categorias(self) -> None:
        self._render_simple_page("categorias.html", "Categorías - TechStore")

    def _handle_creditos(self) -> None:
        self._render_simple_page("creditos.html", "Créditos y pagos - TechStore")

    def _handle_consultas(self) -> None:
        self._render_simple_page("consultas.html", "Consultas - TechStore")

    def _handle_bitacora(self) -> None:
        self._render_simple_page("bitacora.html", "Bitácora de sesiones - TechStore")

    def _handle_registro(self) -> None:
        self._render_simple_page("registro.html", "Registro - TechStore")

    # ---- Reportes PDF ---- #

    def _handle_reporte_factura(self, query: Dict[str, list]) -> None:
        session = self._require_session()
        if not session:
            return
        try:
            venta_id = int(query.get("idVenta", ["0"])[0])
        except ValueError:
            venta_id = 0

        if venta_id <= 0:
            html = render_template(
                "reportes.html",
                {
                    "title": "Reportes - TechStore",
                    "body": "<p>ID de venta inválido.</p>",
                },
            )
            return self._send_html(html, status=400)

        try:
            pdf = REPORTE_SERVICE.factura_venta_pdf(venta_id)
        except Exception as ex:
            html = render_template(
                "reportes.html",
                {
                    "title": "Reportes - TechStore",
                    "body": f"<p>Error al generar factura: {ex}</p>",
                },
            )
            return self._send_html(html, status=500)

        self._send_pdf(pdf, f"factura_{venta_id}.pdf")

    def _handle_reporte_ventas_mes(self, query: Dict[str, list]) -> None:
        session = self._require_session()
        if not session:
            return
        try:
            mes = int(query.get("mes", ["0"])[0])
            anio = int(query.get("anio", ["0"])[0])
            pdf = REPORTE_SERVICE.ventas_mes_pdf(mes, anio)
        except Exception as ex:
            html = render_template(
                "reportes.html",
                {
                    "title": "Reportes - TechStore",
                    "body": f"<p>Error al generar reporte de ventas del mes: {ex}</p>",
                },
            )
            return self._send_html(html, status=500)

        self._send_pdf(pdf, f"ventas_mes_{anio}_{mes:02d}.pdf")

    def _handle_reporte_iva_trimestre(self, query: Dict[str, list]) -> None:
        session = self._require_session()
        if not session:
            return
        try:
            tri = int(query.get("trimestre", ["0"])[0])
            anio = int(query.get("anio", ["0"])[0])
            pdf = REPORTE_SERVICE.iva_trimestre_pdf(tri, anio)
        except Exception as ex:
            html = render_template(
                "reportes.html",
                {
                    "title": "Reportes - TechStore",
                    "body": f"<p>Error al generar reporte de IVA: {ex}</p>",
                },
            )
            return self._send_html(html, status=500)

        self._send_pdf(pdf, f"iva_trimestre_{anio}_T{tri}.pdf")

    def _handle_reporte_ventas_tipo(self, query: Dict[str, list]) -> None:
        session = self._require_session()
        if not session:
            return
        try:
            fi = query.get("fechaInicio", [""])[0]
            ff = query.get("fechaFin", [""])[0]
            pdf = REPORTE_SERVICE.ventas_credito_vs_contado_pdf(fi, ff)
        except Exception as ex:
            html = render_template(
                "reportes.html",
                {
                    "title": "Reportes - TechStore",
                    "body": f"<p>Error al generar reporte de ventas por tipo: {ex}</p>",
                },
            )
            return self._send_html(html, status=500)

        self._send_pdf(pdf, "ventas_credito_vs_contado.pdf")

    def _handle_reporte_inventario_categoria(self) -> None:
        session = self._require_session()
        if not session:
            return
        try:
            pdf = REPORTE_SERVICE.inventario_por_categoria_pdf()
        except Exception as ex:
            html = render_template(
                "reportes.html",
                {
                    "title": "Reportes - TechStore",
                    "body": f"<p>Error al generar reporte de inventario: {ex}</p>",
                },
            )
            return self._send_html(html, status=500)

        self._send_pdf(pdf, "inventario_por_categoria.pdf")

    def _handle_reporte_clientes_mora(self) -> None:
        session = self._require_session()
        if not session:
            return
        try:
            pdf = REPORTE_SERVICE.clientes_morosos_pdf()
        except Exception as ex:
            html = render_template(
                "reportes.html",
                {
                    "title": "Reportes - TechStore",
                    "body": f"<p>Error al generar reporte de clientes morosos: {ex}</p>",
                },
            )
            return self._send_html(html, status=500)

        self._send_pdf(pdf, "clientes_mora.pdf")


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
