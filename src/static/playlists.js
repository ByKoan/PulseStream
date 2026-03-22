document.addEventListener("DOMContentLoaded", () => {

    // ===============================
    // IMPORTAR PLAYLIST YOUTUBE
    // ===============================
    async function importYT() {
        const urlInput = document.getElementById("yt-url");
        if (!urlInput || !urlInput.value.trim()) {
            alert("Introduce una URL válida");
            return;
        }
        const url = urlInput.value.trim();

        try {
            const res = await fetch("/import_youtube_playlist", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ url })
            });
            const data = await res.json();
            alert(data.success ? `Playlist importada correctamente` : `Error: ${data.error}`);
            if (data.success) location.reload();
        } catch (err) {
            alert("Error al importar playlist: " + err);
        }
    }

    window.importYT = importYT; // global para el botón inline

    // ===============================
    // RENOMBRAR PLAYLIST INLINE
    // ===============================
    document.querySelectorAll(".rename-playlist-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const li = btn.closest(".playlist-item");
            const input = li?.querySelector(".rename-input");
            const nameEl = li?.querySelector(".playlist-name");
            const playlistId = btn.dataset.playlist;
            if (!input || !nameEl) return;

            if (input.style.display === "none") {
                input.value = nameEl.textContent.trim();
                input.style.display = "inline-block";
                input.focus();
                return;
            }

            const newName = input.value.trim();
            if (!newName) {
                alert("Nombre inválido");
                return;
            }

            try {
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
    // ELIMINAR PLAYLIST INLINE
    // ===============================
    document.querySelectorAll(".delete-playlist-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const playlistId = btn.dataset.playlist;
            if (!playlistId) return;

            if (!confirm("¿Eliminar esta playlist?")) return;

            try {
                const res = await fetch("/delete_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ playlist_id: playlistId })
                });
                const data = await res.json();
                if (data.success) {
                    btn.closest(".playlist-item")?.remove();
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