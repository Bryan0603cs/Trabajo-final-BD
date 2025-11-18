from services.auth_service import AuthService

if __name__ == "__main__":
    auth = AuthService()
    resultado = auth.login("admin", "admin123", ip="127.0.0.1")

    if resultado is None:
        print("Login fallido :(")
    else:
        print("Login OK para:", resultado.usuario.username)
        print("ID bitácora:", resultado.id_bitacora)
        # Cerramos la sesión para probar el logout:
        auth.logout(resultado.id_bitacora)
        print("Logout registrado.")
