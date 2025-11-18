from dao.usuario_dao import UsuarioDAO

if __name__ == "__main__":
    dao = UsuarioDAO()
    usuarios = dao.listar_todos()

    print("Usuarios en la base de datos:")
    for u in usuarios:
        print(u.id_usuario, u.username, u.nombre_completo)
