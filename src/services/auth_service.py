from werkzeug.security import check_password_hash
from database.db import get_db_connection

def validate_user(username, password):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return True

    return False