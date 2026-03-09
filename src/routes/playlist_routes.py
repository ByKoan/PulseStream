from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for
from database.db import get_db_connection

playlist_bp = Blueprint("playlist", __name__)


@playlist_bp.route("/playlists")
def playlists():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM playlists WHERE user_id = %s",
        (session["user_id"],)
    )

    playlists = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("playlists.html", playlists=playlists)


@playlist_bp.route("/create_playlist", methods=["POST"])
def create_playlist():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    name = request.form.get("name")

    if not name:
        return redirect(url_for("playlist.playlists"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO playlists (name, user_id) VALUES (%s,%s)",
        (name, session["user_id"])
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("playlist.playlists"))

@playlist_bp.route("/playlist/<int:playlist_id>")
def view_playlist(playlist_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM playlists WHERE id=%s AND user_id=%s", 
                       (playlist_id, session['user_id']))
        playlist = cursor.fetchone()

        if not playlist:
            return redirect(url_for("playlist.playlists"))  

        cursor.execute("""
            SELECT song_filename 
            FROM playlist_songs
            WHERE playlist_id = %s
        """, (playlist_id,))
        songs = [row['song_filename'] for row in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()

    return render_template("playlist_view.html", playlist=playlist, songs=songs)