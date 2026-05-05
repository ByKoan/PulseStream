// =============================================================================
// playlists.js — Página de listado de playlists
// Usado en: playlists.html
//
// Responsabilidades:
//   - Menú desplegable de navegación
//   - Contador en tiempo real del número de playlists del usuario
//   - Importar una playlist de YouTube introduciendo su URL
//   - Renombrar una playlist de forma inline (sin recargar la página)
//   - Eliminar una playlist con confirmación
//
// Endpoints que consume:
//   GET  /api/playlist_count        → número actual de playlists del usuario
//   POST /import_youtube_playlist   → importa una playlist de YouTube
//   POST /rename_playlist           → cambia el nombre de una playlist
//   POST /delete_playlist           → elimina una playlist
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {

    // ===============================
    // MENÚ DESPLEGABLE DE NAVEGACIÓN
    // ===============================
    window.toggleMenu = function () {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    // Cierra el menú si el usuario hace clic fuera de él
    document.addEventListener("click", function (e) {
        const menu = document.getElementById("dropdownMenu");
        const btn = document.querySelector(".menu-toggle");
        if (!menu || !btn) return;
        if (!menu.contains(e.target) && !btn.contains(e.target)) {
            menu.classList.remove("show");
        }
    });

    // ===============================
    // CONTADOR DE PLAYLISTS EN TIEMPO REAL
    // Actualiza el texto "X playlist(s)" en el encabezado de la página.
    // Se actualiza desde el servidor cada 5 segundos. Si la petición falla,
    // cuenta los elementos .playlist-item visibles en el DOM como fallback.
    // ===============================

    // Actualiza los elementos del DOM con el número de playlists
    function updatePlaylistCounter(count) {
        const numEl = document.getElementById("playlist-count-num");
        const pluralEl = document.getElementById("playlist-count-plural");
        if (!numEl) return;
        numEl.textContent = count;
        // Añade "s" solo si hay más de 1 playlist (pluralización simple en castellano)
        if (pluralEl) pluralEl.textContent = count !== 1 ? "s" : "";
    }

    // Fallback: cuenta los elementos .playlist-item visibles en el DOM
    function updateCounterFromDOM() {
        const count = document.querySelectorAll(".playlist-item").length;
        updatePlaylistCounter(count);
    }

    // Petición al servidor para obtener el conteo real desde la BD
    async function pollPlaylistCount() {
        try {
            const res = await fetch("/api/playlist_count");
            if (!res.ok) return; // Si falla (ej: 401), no actualiza
            const data = await res.json();
            updatePlaylistCounter(data.count);
        } catch (err) {
            // Si hay error de red, usamos el conteo del DOM
            updateCounterFromDOM();
        }
    }

    // Lanza el polling cada 5 segundos
    setInterval(pollPlaylistCount, 5000);

    // ===============================
    // IMPORTAR PLAYLIST DE YOUTUBE
    // Toma la URL del input #yt-url y la envía al backend.
    // El backend descarga todos los vídeos de la playlist en audio MP3
    // y los registra en la BD. Recarga la página al terminar.
    // Expuesto como window.importYT para poder llamarlo desde onclick en el HTML.
    // ===============================
    async function importYT() {
        const urlInput = document.getElementById("yt-url");
        if (!urlInput || !urlInput.value.trim()) {
            alert("Introduce una URL válida");
            return;
        }
        const url = urlInput.value.trim();

        try {
            // POST /import_youtube_playlist — puede tardar varios minutos según el tamaño
            const res = await fetch("/import_youtube_playlist", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });
            const data = await res.json();
            alert(data.success
                ? "Playlist importada correctamente"
                : `Error: ${data.error}`
            );
            if (data.success) location.reload(); // Recarga para mostrar la nueva playlist
        } catch (err) {
            alert("Error al importar playlist: " + err);
        }
    }

    window.importYT = importYT;

    // ===============================
    // RENOMBRAR PLAYLIST (inline)
    // Cada botón .rename-playlist-btn alterna la visibilidad del input de texto
    // dentro del mismo elemento de lista. En el primer clic muestra el input;
    // en el segundo clic envía el nuevo nombre al servidor.
    // ===============================
    document.querySelectorAll(".rename-playlist-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const li = btn.closest(".playlist-item");
            const input = li?.querySelector(".rename-input");
            const nameEl = li?.querySelector(".playlist-name");
            const playlistId = btn.dataset.playlist;
            if (!input || !nameEl) return;

            // Primer clic: mostrar el input con el nombre actual
            if (input.style.display === "none") {
                input.value = nameEl.textContent.trim();
                input.style.display = "inline-block";
                input.focus();
                return;
            }

            // Segundo clic: enviar el nuevo nombre al backend
            const newName = input.value.trim();
            if (!newName) {
                alert("Nombre inválido");
                return;
            }

            try {
                // POST /rename_playlist
                const res = await fetch("/rename_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ playlist_id: playlistId, name: newName })
                });
                const data = await res.json();
                if (data.success) location.reload();
                else alert(data.error);
            } catch (err) {
                alert("Error: " + err);
            }
        });
    });

    // ===============================
    // ELIMINAR PLAYLIST
    // Pide confirmación antes de eliminar. Si el servidor confirma el éxito,
    // elimina el elemento del DOM sin recargar y actualiza el contador.
    // ===============================
    document.querySelectorAll(".delete-playlist-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const playlistId = btn.dataset.playlist;
            if (!playlistId) return;

            if (!confirm("¿Eliminar esta playlist?")) return;

            try {
                // POST /delete_playlist
                const res = await fetch("/delete_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ playlist_id: playlistId })
                });
                const data = await res.json();
                if (data.success) {
                    // Elimina el elemento del DOM directamente (sin recargar)
                    btn.closest(".playlist-item")?.remove();
                    // Actualiza el contador inmediatamente usando el DOM como fuente
                    updateCounterFromDOM();
                    alert("Playlist eliminada correctamente");
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (err) {
                alert("Error al eliminar playlist: " + err);
            }
        });
    });
});
