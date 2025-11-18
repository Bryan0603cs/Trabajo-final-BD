from __future__ import annotations

import oracledb

# -------------- AJUSTA ESTOS DATOS A TU ENTORNO -----------------
DB_USER = "SYSTEM"
DB_PASSWORD = "12345"
DB_DSN = "localhost:1521/xe"   # cámbialo si tu servicio no es "orcl"
# ----------------------------------------------------------------


def get_connection() -> oracledb.Connection:
    """
    Devuelve una conexión nueva a Oracle.
    """
    # Versión compatible con drivers antiguos que no aceptan 'encoding'
    return oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=DB_DSN,
    )


def test_connection() -> bool:
    """
    Prueba rápida de conexión.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM DUAL")
        cur.fetchone()
        print("[OK] Conexión a Oracle exitosa.")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] No se pudo conectar a Oracle: {exc}")
        return False
    finally:
        if conn is not None:
            conn.close()
