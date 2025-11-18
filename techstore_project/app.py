from __future__ import annotations
from config.db_config import get_connection

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
ROLE_ESPORADICO_ID = 3  # Esporádico


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
# Helpers de base de datos (solo lecturas simples)
# ---------------------------------------------------------------------------

def db_fetch_all(sql: str, params: Optional[Dict] = None) -> list[dict]:
    """
    Ejecuta un SELECT y devuelve una lista de diccionarios.
    Las claves del diccionario son los nombres de las columnas en minúsculas.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or {})
        cols = [c[0].lower() for c in cur.description]
        rows = []
        for row in cur:
            rows.append(dict(zip(cols, row)))
        cur.close()
        return rows
    finally:
        conn.close()


def build_html_table(headers: list[str], fields: list[str], rows: list[dict]) -> str:
    """
    Construye una tabla HTML a partir de una lista de diccionarios.
    """
    html = []
    html.append('<div class="ts-table-wrapper">')
    html.append('<table class="ts-table">')
    html.append('<thead><tr>')
    for h in headers:
        html.append(f'<th>{h}</th>')
    html.append('</tr></thead><tbody>')

    if not rows:
        html.append(
            f'<tr><td colspan="{len(headers)}" class="ts-empty">No hay registros.</td></tr>'
        )
    else:
        for row in rows:
            html.append('<tr>')
            for field in fields:
                value = row.get(field)
                if value is None:
                    value = ""
                html.append(f'<td>{value}</td>')
            html.append('</tr>')

    html.append('</tbody></table></div>')
    return "".join(html)


def build_page(title: str, body_html: str) -> str:
    """
    Construye una página HTML completa, sin depender de las plantillas estáticas.
    Esto garantiza que se muestren los datos reales (ventas, bitácora, etc.).
    """
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                         Roboto, Helvetica, Arial, sans-serif;
            background: #f3f4ff;
            color: #111827;
        }}
        header.ts-header {{
            background: #4f46e5;
            color: #ffffff;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        header.ts-header h1 {{
            margin: 0;
            font-size: 1.4rem;
        }}
        header.ts-header nav a {{
            color: #e0e7ff;
            margin-left: 1rem;
            text-decoration: none;
            font-size: 0.95rem;
        }}
        header.ts-header nav a:hover {{
            text-decoration: underline;
        }}
        main.ts-main {{
            max-width: 1100px;
            margin: 1.5rem auto 2rem;
            padding: 1.5rem;
            background: #ffffff;
            border-radius: 0.75rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        }}
        main.ts-main h2 {{
            margin-top: 0;
            color: #1e293b;
        }}
        .ts-table-wrapper {{
            margin-top: 1rem;
            overflow-x: auto;
        }}
        .ts-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        .ts-table th,
        .ts-table td {{
            border-bottom: 1px solid #e5e7eb;
            padding: 0.6rem 0.75rem;
            text-align: left;
            vertical-align: top;
        }}
        .ts-table th {{
            background: #eef2ff;
            font-weight: 600;
            color: #374151;
        }}
        .ts-table tr:nth-child(even) td {{
            background: #f9fafb;
        }}
        .ts-empty {{
            text-align: center;
            color: #6b7280;
            font-style: italic;
        }}
        .ts-actions a {{
            color: #4f46e5;
            text-decoration: none;
            font-weight: 500;
        }}
        .ts-actions a:hover {{
            text-decoration: underline;
        }}
        ul.ts-menu-list {{
            list-style: none;
            padding-left: 0;
        }}
        ul.ts-menu-list li {{
            margin: 0.25rem 0;
        }}
        ul.ts-menu-list a {{
            color: #4f46e5;
            text-decoration: none;
        }}
        ul.ts-menu-list a:hover {{
            text-decoration: underline;
        }}
        .ts-subtitle {{
            color: #6b7280;
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }}
    </style>
</head>
<body>
<header class="ts-header">
    <h1>TechStore</h1>
    <nav>
        <a href="/menu">Menú principal</a>
        <a href="/entidades">Entidades</a>
        <a href="/ventas">Ventas</a>
        <a href="/reportes">Reportes</a>
        <a href="/utilidades">Utilidades</a>
        <a href="/logout">Cerrar sesión</a>
    </nav>
</header>
<main class="ts-main">
{body_html}
</main>
</body>
</html>
"""


def render_template(template_name: str, context: Optional[Dict[str, str]] = None) -> str:
    """
    Carga un archivo HTML de templates/ y reemplaza {{placeholders}}.
    Usado solo para login, menú y páginas “documentación”.
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

    # -------------------------------------------------------------------
    # Control de roles
    # -------------------------------------------------------------------
    def _require_session_and_level(self, allowed_levels: list[int]) -> Optional[Session]:
        """
        Obtiene la sesión y verifica que el nivel esté permitido.
        Si no hay sesión -> redirige a /login
        Si no tiene permisos -> 403
        """
        session = self._require_session()
        if not session:
            return None

        if session.nivel not in allowed_levels:
            self.send_error(403, "No tiene permisos para esta opción")
            return None

        return session

    # Evitar que http.server imprima cada request en consola
    def log_message(self, format: str, *args) -> None:  # noqa: A003
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

        # ENTIDADES
        if path in ("/entidades", "/entidades.html"):
            return self._handle_entidades()

        if path in ("/usuarios", "/usuarios.html"):
            return self._handle_usuarios()

        if path in ("/clientes", "/clientes.html"):
            return self._handle_clientes()

        if path in ("/productos", "/productos.html"):
            return self._handle_productos()

        if path in ("/categorias", "/categorias.html"):
            return self._handle_categorias()

        if path in ("/proveedores", "/proveedores.html"):
            return self._handle_proveedores()

        # TRANSACCIONES / VENTAS
        if path in ("/transacciones", "/transacciones.html", "/ventas", "/ventas.html"):
            return self._handle_ventas()

        if path in ("/creditos", "/creditos.html"):
            return self._handle_creditos()

        # REPORTES / UTILIDADES / AYUDAS
        if path in ("/reportes", "/reportes.html"):
            return self._handle_reportes()

        if path in ("/utilidades", "/utilidades.html"):
            return self._handle_utilidades()

        if path in ("/bitacora", "/bitacora.html"):
            return self._handle_bitacora()

        if path in ("/consultas", "/consultas.html"):
            return self._handle_consultas()

        if path in ("/ayudas", "/ayudas.html"):
            return self._handle_ayudas()

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

        # Aquí podrás ir añadiendo más POST (registro de ventas, CRUD, etc.)
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

    # ---- Secciones de menú genéricas (con plantillas estáticas) ---- #

    def _require_session(self) -> Optional[Session]:
        """
        Obtiene la sesión o redirige a /login si no hay usuario autenticado.
        """
        session = self._get_current_session()
        if not session:
            self._redirect("/login")
            return None
        return session

    def _render_simple_page(
        self,
        template: str,
        title: str,
        extra_ctx: Optional[Dict[str, str]] = None,
    ) -> None:
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
        nombre = getattr(usuario, "nombre_completo", None) or getattr(
            usuario, "nombre", ""
        )
        self._render_simple_page(
            "menu_principal.html",
            "Menú principal - TechStore",
            {"usuario_nombre": nombre},
        )

    # -------------------------------------------------------------------
    # ENTIDADES (menus y listados reales)
    # -------------------------------------------------------------------

    def _handle_entidades(self) -> None:
        session = self._require_session()
        if not session:
            return

        opciones = []
        if session.nivel == 1:
            opciones.append('<li><a href="/usuarios">Usuarios del sistema</a></li>')

        opciones.extend(
            [
                '<li><a href="/clientes">Clientes</a></li>',
                '<li><a href="/categorias">Categorías</a></li>',
                '<li><a href="/proveedores">Proveedores</a></li>',
                '<li><a href="/productos">Productos</a></li>',
            ]
        )

        body = f"""
        <h2>Entidades</h2>
        <p class="ts-subtitle">
            Seleccione la entidad que desea consultar o administrar.
        </p>
        <ul class="ts-menu-list">
            {''.join(opciones)}
        </ul>
        """
        html = build_page("Entidades - TechStore", body)
        self._send_html(html)

    def _handle_usuarios(self) -> None:
        session = self._require_session_and_level([1])  # Solo admin
        if not session:
            return

        rows = db_fetch_all(
            """
            SELECT
                u.id_usuario,
                u.nombre || ' ' || u.apellido AS nombre_completo,
                u.username,
                r.nombre_rol AS rol,
                u.estado
            FROM usuarios u
            JOIN roles r ON r.id_rol = u.id_rol
            ORDER BY u.id_usuario
            """
        )

        tabla = build_html_table(
            headers=["ID", "Nombre completo", "Usuario", "Rol", "Estado"],
            fields=["id_usuario", "nombre_completo", "username", "rol", "estado"],
            rows=rows,
        )

        body = f"""
        <h2>Usuarios del sistema</h2>
        <p class="ts-subtitle">
            Usuarios internos divididos por niveles (ADMIN, PARAMÉTRICO, ESPORÁDICO).
        </p>
        {tabla}
        """
        html = build_page("Usuarios - TechStore", body)
        self._send_html(html)

    def _handle_clientes(self) -> None:
        session = self._require_session_and_level([1, 2, 3])
        if not session:
            return

        rows = db_fetch_all(
            """
            SELECT
                id_cliente,
                nombre,
                apellido,
                documento,
                telefono,
                email
            FROM clientes
            ORDER BY id_cliente
            """
        )

        tabla = build_html_table(
            headers=["ID", "Nombre", "Apellido", "Documento", "Teléfono", "Email"],
            fields=["id_cliente", "nombre", "apellido", "documento", "telefono", "email"],
            rows=rows,
        )

        body = f"""
        <h2>Clientes</h2>
        <p class="ts-subtitle">
            Listado de clientes registrados en la tienda.
        </p>
        {tabla}
        """
        html = build_page("Clientes - TechStore", body)
        self._send_html(html)

    def _handle_categorias(self) -> None:
        session = self._require_session_and_level([1, 2, 3])
        if not session:
            return

        rows = db_fetch_all(
            """
            SELECT
                id_categoria,
                nombre,
                descripcion
            FROM categorias
            ORDER BY id_categoria
            """
        )

        tabla = build_html_table(
            headers=["ID", "Nombre", "Descripción"],
            fields=["id_categoria", "nombre", "descripcion"],
            rows=rows,
        )

        body = f"""
        <h2>Categorías de productos</h2>
        {tabla}
        """
        html = build_page("Categorías - TechStore", body)
        self._send_html(html)

    def _handle_proveedores(self) -> None:
        session = self._require_session_and_level([1, 2, 3])
        if not session:
            return

        rows = db_fetch_all(
            """
            SELECT
                id_proveedor,
                nombre,
                telefono,
                email,
                direccion
            FROM proveedores
            ORDER BY id_proveedor
            """
        )

        tabla = build_html_table(
            headers=["ID", "Nombre", "Teléfono", "Email", "Dirección"],
            fields=["id_proveedor", "nombre", "telefono", "email", "direccion"],
            rows=rows,
        )

        body = f"""
        <h2>Proveedores</h2>
        {tabla}
        """
        html = build_page("Proveedores - TechStore", body)
        self._send_html(html)

    def _handle_productos(self) -> None:
        session = self._require_session_and_level([1, 2, 3])
        if not session:
            return

        rows = db_fetch_all(
            """
            SELECT
                p.id_producto,
                p.nombre,
                c.nombre AS categoria,
                pr.nombre AS proveedor,
                p.precio_venta,
                p.stock
            FROM productos p
            JOIN categorias c ON c.id_categoria = p.id_categoria
            LEFT JOIN proveedores pr ON pr.id_proveedor = p.id_proveedor
            ORDER BY p.id_producto
            """
        )

        tabla = build_html_table(
            headers=["ID", "Nombre", "Categoría", "Proveedor", "Precio venta", "Stock"],
            fields=[
                "id_producto",
                "nombre",
                "categoria",
                "proveedor",
                "precio_venta",
                "stock",
            ],
            rows=rows,
        )

        body = f"""
        <h2>Productos</h2>
        <p class="ts-subtitle">
            Productos disponibles con su categoría, proveedor y stock actual.
        </p>
        {tabla}
        """
        html = build_page("Productos - TechStore", body)
        self._send_html(html)

    # -------------------------------------------------------------------
    # VENTAS / CREDITOS
    # -------------------------------------------------------------------

    def _handle_ventas(self) -> None:
        # Nivel 1 y 2 registran; 3 consulta. Todos pueden ver.
        session = self._require_session_and_level([1, 2, 3])
        if not session:
            return

        rows = db_fetch_all(
            """
            SELECT
                v.id_venta,
                TO_CHAR(v.fecha, 'YYYY-MM-DD HH24:MI') AS fecha,
                u.username AS usuario,
                c.nombre || ' ' || c.apellido AS cliente,
                CASE v.es_credito
                    WHEN 'S' THEN 'Crédito'
                    ELSE 'Contado'
                END AS tipo,
                v.total
            FROM ventas v
            JOIN usuarios u ON u.id_usuario = v.id_usuario
            JOIN clientes c ON c.id_cliente = v.id_cliente
            ORDER BY v.fecha DESC
            """
        )

        tabla = build_html_table(
            headers=["ID", "Fecha", "Usuario", "Cliente", "Tipo", "Total"],
            fields=["id_venta", "fecha", "usuario", "cliente", "tipo", "total"],
            rows=rows,
        )

        body = f"""
        <h2>Ventas registradas</h2>
        <p class="ts-subtitle">
            Listado de todas las ventas realizadas (contado y crédito).
        </p>
        {tabla}
        """
        html = build_page("Ventas - TechStore", body)
        self._send_html(html)

    def _handle_creditos(self) -> None:
        session = self._require_session_and_level([1, 2, 3])
        if not session:
            return

        rows = db_fetch_all(
            """
            SELECT
                cr.id_credito,
                v.id_venta,
                c.nombre || ' ' || c.apellido AS cliente,
                cr.saldo_total,
                cr.saldo_pendiente,
                TO_CHAR(cr.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
                cr.estado
            FROM creditos cr
            JOIN ventas v ON v.id_venta = cr.id_venta
            JOIN clientes c ON c.id_cliente = v.id_cliente
            ORDER BY cr.id_credito
            """
        )

        tabla = build_html_table(
            headers=[
                "ID Crédito",
                "ID Venta",
                "Cliente",
                "Saldo total",
                "Saldo pendiente",
                "Vencimiento",
                "Estado",
            ],
            fields=[
                "id_credito",
                "id_venta",
                "cliente",
                "saldo_total",
                "saldo_pendiente",
                "fecha_vencimiento",
                "estado",
            ],
            rows=rows,
        )

        body = f"""
        <h2>Créditos</h2>
        <p class="ts-subtitle">
            Créditos generados a partir de ventas a crédito, con su estado actual.
        </p>
        {tabla}
        """
        html = build_page("Créditos - TechStore", body)
        self._send_html(html)

    # -------------------------------------------------------------------
    # BITÁCORA (solo admin) y otras secciones documentales
    # -------------------------------------------------------------------

    def _handle_bitacora(self) -> None:
        # Bitácora solo tiene sentido que la vea el ADMIN
        session = self._require_session_and_level([1])
        if not session:
            return

        rows = db_fetch_all(
            """
            SELECT
                b.id_bitacora,
                u.username,
                TO_CHAR(b.fecha_login,  'YYYY-MM-DD HH24:MI:SS') AS fecha_login,
                TO_CHAR(b.fecha_logout, 'YYYY-MM-DD HH24:MI:SS') AS fecha_logout,
                b.ip,
                b.detalle
            FROM bitacora_sesion b
            JOIN usuarios u ON u.id_usuario = b.id_usuario
            ORDER BY b.fecha_login DESC
            """
        )

        tabla = build_html_table(
            headers=["ID", "Usuario", "Login", "Logout", "IP", "Detalle"],
            fields=[
                "id_bitacora",
                "username",
                "fecha_login",
                "fecha_logout",
                "ip",
                "detalle",
            ],
            rows=rows,
        )

        body = f"""
        <h2>Bitácora de sesiones</h2>
        <p class="ts-subtitle">
            Registros de ingreso y salida de los usuarios del sistema.
        </p>
        {tabla}
        """
        html = build_page("Bitácora - TechStore", body)
        self._send_html(html)

    # Estas secciones siguen usando las plantillas “documentales”

    def _handle_reportes(self) -> None:
        self._render_simple_page("reportes.html", "Reportes y consultas - TechStore")

    def _handle_utilidades(self) -> None:
        self._render_simple_page("utilidades.html", "Utilidades - TechStore")

    def _handle_ayudas(self) -> None:
        self._render_simple_page("ayudas.html", "Ayudas - TechStore")

    def _handle_consultas(self) -> None:
        self._render_simple_page("consultas.html", "Consultas - TechStore")

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
