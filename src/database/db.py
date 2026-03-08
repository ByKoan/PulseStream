import mysql.connector
import time
import os
from config import Config
from mysql.connector import Error


def get_db_connection(retries=10, delay=3):
    for i in range(retries):
        try:
            conn = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            return conn
        except Error as e:
            print(f"Intento {i+1}/{retries} fallido: {e}")
            time.sleep(delay)

    raise Exception("No se pudo conectar a la base de datos después de varios intentos")


def create_user_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "resources", "script.sql")
        )

        with open(script_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        for statement in sql_script.split(";"):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)

        print("Base de datos y tabla(s) creadas correctamente desde script.sql")

    finally:
        conn.commit()
        cursor.close()
        conn.close()


def get_user_role(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT role FROM users WHERE username = %s",
            (username,)
        )

        user = cursor.fetchone()

        if user:
            return user["role"]

        return None

    finally:
        cursor.close()
        conn.close()


def get_user_ban(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT banned_until FROM users WHERE username = %s",
            (username,)
        )

        user = cursor.fetchone()

        if user:
            return user["banned_until"]

        return None

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_user_db()