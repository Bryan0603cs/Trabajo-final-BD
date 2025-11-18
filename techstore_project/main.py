from __future__ import annotations

"""
Punto de entrada de la aplicación TechStore.

Cumple con:
- Arrancar el servidor HTTP sin frameworks (app.run_server).
- Deja espacio para que en el futuro se agreguen otros modos de ejecución
  (por ejemplo, menú por consola si el profesor lo llegara a pedir).
"""

from app import run_server


def main() -> None:
    """
    Arranca el servidor web en http://localhost:8000
    """
    print("==============================================")
    print("        TECHSTORE - PROYECTO BASES DE DATOS   ")
    print("==============================================")
    print("Servidor web sin frameworks (http.server)")
    print("URL: http://localhost:8000")
    print("Presiona Ctrl+C para detener el servidor.")
    print("==============================================")

    run_server(host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
