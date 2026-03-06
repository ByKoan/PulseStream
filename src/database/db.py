import mysql.connector
import time
from config import Config

import time
import mysql.connector
from mysql.connector import Error

def get_db_connection(retries=10, delay=3):
    for i in range(retries):
        try:
            conn = mysql.connector.connect(
                host="db",
                user="root",
                password="root",
                database="music_db"
            )
            return conn
        except Error as e:
            print(f"Intento {i+1}/{retries} fallido: {e}")
            time.sleep(delay)
    raise Exception("No se pudo conectar a la base de datos después de varios intentos")


def create_user_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()