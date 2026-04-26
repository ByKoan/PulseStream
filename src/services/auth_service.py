from werkzeug.security import check_password_hash  # Función para verificar contraseñas cifradas
from database.db import get_db_connection  # Función para conectarse a la base de datos

def validate_user(username, password):
    # Establece conexión con la base de datos
    conn = get_db_connection()
    
    # Crea un cursor que devuelve resultados como diccionarios (clave = nombre de columna)
    cursor = conn.cursor(dictionary=True)

    # Ejecuta una consulta SQL para buscar el usuario por su nombre
    # %s es un placeholder para evitar inyección SQL
    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    # Obtiene el primer resultado de la consulta (si existe)
    user = cursor.fetchone()

    # Cierra el cursor y la conexión (muy importante para liberar recursos)
    cursor.close()
    conn.close()

    # Verifica:
    # 1. Que el usuario exista
    # 2. Que la contraseña introducida coincida con la almacenada (hasheada)
    if user and check_password_hash(user['password'], password):
        return True  # Credenciales correctas

    # Si no existe el usuario o la contraseña no coincide
    return False