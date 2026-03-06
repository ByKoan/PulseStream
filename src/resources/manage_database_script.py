from werkzeug.security import generate_password_hash, check_password_hash
from colorama import Fore, Style, init
from colorama.ansi import clear_screen
from mysql.connector import connect, Error, IntegrityError
from getpass import getpass, _raw_input
from sys import exit
import sys
import os
import time

# =========================
# Añadimos la carpeta src al path para que pueda importar config
# =========================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config

# =========================
# CONFIG MYSQL (DESDE ENV)
# =========================
DB_CONFIG = {
    "host": Config.DB_HOST,
    "user": Config.DB_USER,
    "password": Config.DB_PASSWORD,
    "database": Config.DB_NAME,
    "auth_plugin": "mysql_native_password"  # importante para compatibilidad
}

MAX_RETRIES = 10
RETRY_DELAY = 3  # segundos

def raw_input_(prompt):
    while True:
        try:
            return _raw_input(prompt)
        except KeyboardInterrupt:
            print("\r")

# =========================
# CONEXIÓN MYSQL CON REINTENTOS
# =========================
def get_db_connection():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = connect(**DB_CONFIG)
            return conn
        except Error as e:
            print(Fore.RED + f"Intento {attempt}/{MAX_RETRIES} fallido: {e}")
            time.sleep(RETRY_DELAY)
    raise Exception("No se pudo conectar a la base de datos después de varios intentos")


# =========================
# CREAR TABLA
# =========================
def create_user_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
        """)
    finally:
        conn.commit()
        cursor.close()
        conn.close()


# =========================
# AÑADIR USUARIO
# =========================
def add_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
    finally:
        conn.commit()
        cursor.close()
        conn.close()


# =========================
# VALIDAR USUARIO
# =========================
def validate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return user and check_password_hash(user["password"], password)


# =========================
# MOSTRAR USUARIOS
# =========================
def show_users(print=print):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    if users:
        print("\n" + Fore.GREEN + f"{'ID':<5}{'Username':<20}{'Password (Hash)'}")
        for user in users:
            print(Fore.CYAN + f"{user['id']:<5}{user['username']:<20}{user['password']}")
    else:
        print(Fore.RED + "No hay usuarios en la base de datos.")

    print("\n")
    return users


# =========================
# CREAR USUARIO
# =========================
def create_user():
    while True:
        username = raw_input_(Fore.YELLOW + "Ingresa el nombre de usuario: ")
        password = getpass(Fore.YELLOW + "Ingresa la contraseña: ")

        try:
            add_user(username, password)
            print(Fore.GREEN + "\nUsuario creado exitosamente.\n")
            break
        except IntegrityError:
            print(Fore.RED + "\nUsuario ya existente.\n")


# =========================
# ELIMINAR USUARIO
# =========================
def delete_user():
    def print_nothing(*args, **kwargs): pass

    show_users(print=print_nothing)
    username = raw_input_(Fore.YELLOW + "Ingresa el nombre del usuario a eliminar: ")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        if cursor.rowcount == 0:
            print(Fore.RED + f"\nEl usuario {username} no existe.\n")
        else:
            print(Fore.GREEN + f"\nUsuario {username} eliminado exitosamente.\n")
    finally:
        conn.commit()
        cursor.close()
        conn.close()


# =========================
# CAMBIAR PASSWORD
# =========================
def change_password():
    username = raw_input_(Fore.YELLOW + "Ingresa el nombre del usuario: ")
    new_password = getpass(Fore.YELLOW + "Ingresa la nueva contraseña: ")
    hashed_password = generate_password_hash(new_password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET password = %s WHERE username = %s",
            (hashed_password, username)
        )
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    print(Fore.GREEN + f"\nContraseña del usuario {username} cambiada exitosamente.\n")


# =========================
# CAMBIAR USERNAME
# =========================
def change_username():
    old_username = raw_input_(Fore.YELLOW + "Ingresa el nombre actual: ")
    new_username = raw_input_(Fore.YELLOW + "Ingresa el nuevo nombre: ")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET username = %s WHERE username = %s",
            (new_username, old_username)
        )
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    print(Fore.GREEN + f"\nNombre cambiado exitosamente.\n")


# =========================
# MENÚ
# =========================
def show_menu():
    print(Fore.MAGENTA + Style.BRIGHT + "\nMade By Koan")
    print(Fore.MAGENTA + Style.BRIGHT + "\nMenú de Opciones:")
    print(Fore.CYAN + "1. Crear usuario")
    print(Fore.CYAN + "2. Eliminar usuario")
    print(Fore.CYAN + "3. Cambiar contraseña")
    print(Fore.CYAN + "4. Cambiar nombre")
    print(Fore.CYAN + "5. Ver usuarios")
    print(Fore.RED + "6. Salir")


# =========================
# MAIN
# =========================
def main():
    create_user_db()
    options = [
        create_user,
        delete_user,
        change_password,
        change_username,
        show_users
    ]

    print(clear_screen())
    while True:
        show_menu()
        try:
            choice = int(raw_input_(Fore.YELLOW + "Selecciona una opción: "))
            if 1 <= choice <= len(options):
                options[choice - 1]()
            elif choice == 6:
                print(Fore.RED + "\nSaliendo...\n")
                exit(0)
            else:
                raise ValueError
        except ValueError:
            print(Fore.RED + "\nOpción no válida.\n")
        raw_input_("presione una tecla para continuar...")
        print(clear_screen())


if __name__ == "__main__":
    init(autoreset=True)
    main()