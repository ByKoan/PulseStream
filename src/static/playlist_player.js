// =============================================================================
// playlist_player.js — Reproductor de una playlist individual
// Usado en: playlist.html (vista de una playlist concreta)
//
// Responsabilidades:
//   - Menú desplegable de navegación
//   - Reproducir canciones del array global window.songs (canciones de la playlist)
//   - Controles: play/pause, siguiente, anterior
//   - Modos: shuffle (aleatorio) y loop (repetición)
//   - Integración con la Media Session API (controles del SO/auriculares)
//   - Clic en canción de la lista para reproducirla por nombre
//   - Buscador de canciones en tiempo real (filtro por nombre)
//   - Eliminar canción de la playlist (sin borrarla de la biblioteca)
//   - Sincronizar playlist con YouTube (actualiza canciones desde la fuente YT)
//   - Contador de canciones de la playlist
//
// Diferencias clave respecto a player.js:
//   - playSongByName() busca por nombre en vez de por índice
//   - Tiene el botón "Sincronizar con YouTube" (syncYtBtn)
//   - Eliminar = quitar de la playlist, no borrar de la biblioteca
//   - El contador muestra "en esta playlist" en vez de "en tu biblioteca"
//   - No tiene el menú de añadir a playlist (ya estás dentro de una)
//
// Datos de entrada:
//   window.songs → array de nombres de archivo de las canciones de la playlist
//
// Endpoints que consume:
//   GET  /play/<filename>           → stream de audio de la canción
//   POST /remove_from_playlist      → elimina una canción de esta playlist
//   POST /sync_youtube_playlist     → sincroniza la playlist con YouTube
//
// Funciones expuestas globalmente (para onclick en el HTML):
//   window.playPause()
//   window.handleNextClick()
//   window.handlePreviousClick()
//   window.toggleShuffle()
//   window.toggleLoop()
//   window.toggleMenu()
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {

    // Wrapper seguro para acceder al array de canciones
    function getSongs() {
        return window.songs || [];
    }

    // Referencias a los elementos del reproductor en el DOM
    const player = document.getElementById("player");
    const audioSource = document.getElementById("audioSource");
    const currentSongTitle = document.getElementById("currentSongTitle");
    const songList = document.getElementById("songList");
    const shuffleToggle = document.getElementById("shuffleToggle");
    const shuffleContainer = document.getElementById("shuffleToggleContainer");
    const loopToggle = document.getElementById("loopToggle");
    const loopContainer = document.getElementById("loopToggleContainer");

    // Estado del reproductor
    let currentSongIndex = 0;
    let shuffle = false;
    let loop = false;

    // ===============================
    // MENÚ DESPLEGABLE DE NAVEGACIÓN
    // ===============================
    window.toggleMenu = function () {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    document.addEventListener("click", function (e) {
        const menu = document.getElementById("dropdownMenu");
        const btn = document.querySelector(".menu-toggle");
        if (!menu || !btn) return;
        if (!menu.contains(e.target) && !btn.contains(e.target)) {
            menu.classList.remove("show");
        }
    });

    // ===============================
    // CARGAR Y REPRODUCIR CANCIÓN
    // Similar a player.js pero opera sobre las canciones de la playlist.
    // Actualiza la fuente del <audio>, lo carga, lo reproduce y configura
    // la Media Session API para controles del sistema operativo.
    // ===============================
    function loadSong(index) {
        const songs = getSongs();
        if (!songs.length || !player || !audioSource) return;

        // Wrapping circular en los extremos del array
        if (index < 0) index = songs.length - 1;
        if (index >= songs.length) index = 0;

        currentSongIndex = index;
        const song = songs[currentSongIndex];

        audioSource.src = "/play/" + encodeURIComponent(song);
        player.load();
        player.play().catch(() => {}); // Silencia el error si el autoplay está bloqueado

        if (currentSongTitle) currentSongTitle.textContent = song;
        document.title = song;

        // Integración con controles del SO, auriculares Bluetooth, pantalla de bloqueo
        if ("mediaSession" in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: song,
                artist: "Koan",
                album: "MusicCloudServer",
                artwork: [{ src: "https://via.placeholder.com/96", sizes: "96x96", type: "image/png" }]
            });
            navigator.mediaSession.setActionHandler("play", () => player.play());
            navigator.mediaSession.setActionHandler("pause", () => player.pause());
            navigator.mediaSession.setActionHandler("nexttrack", handleNextClick);
            navigator.mediaSession.setActionHandler("previoustrack", handlePreviousClick);
        }
    }

    // ===============================
    // CONTROLES DE REPRODUCCIÓN
    // ===============================

    function playPause() {
        if (!player) return;
        player.paused ? player.play() : player.pause();
    }

    // Siguiente canción: aleatoria (shuffle) o la siguiente en orden
    function handleNextClick() {
        const songs = getSongs();
        if (!songs.length) return;

        if (shuffle)
            currentSongIndex = Math.floor(Math.random() * songs.length);
        else
            currentSongIndex = (currentSongIndex + 1) % songs.length;

        loadSong(currentSongIndex);
    }

    // Canción anterior:
    //   - Si lleva más de 3 segundos → reinicia desde el principio
    //   - Si lleva menos de 3 segundos → va a la canción anterior
    //   Nota: en playlist_player no hay shuffle en "anterior" (a diferencia de player.js)
    function handlePreviousClick() {
        const songs = getSongs();
        if (!songs.length || !player) return;

        if (player.currentTime > 3) {
            player.currentTime = 0;
            return;
        }

        currentSongIndex--;
        if (currentSongIndex < 0)
            currentSongIndex = songs.length - 1;

        loadSong(currentSongIndex);
    }

    // ===============================
    // MODOS: SHUFFLE Y LOOP
    // Actualizan tanto el estado interno como la clase CSS "active" del botón.
    // Los listeners están en los contenedores (#shuffleToggleContainer / #loopToggleContainer)
    // para mayor área de clic.
    // ===============================
    function toggleShuffle() {
        shuffle = !shuffle;
        shuffleToggle?.classList.toggle("active", shuffle);
    }

    function toggleLoop() {
        loop = !loop;
        player.loop = loop; // Delega el loop al elemento <audio> nativo
        loopToggle?.classList.toggle("active", loop);
    }

    shuffleContainer?.addEventListener("click", toggleShuffle);
    loopContainer?.addEventListener("click", toggleLoop);

    // ===============================
    // CLIC EN CANCIÓN DE LA LISTA (por nombre)
    // A diferencia de player.js (que busca por índice), aquí se busca la canción
    // por nombre porque en playlists el orden puede diferir del array songs.
    // ===============================
    function playSongByName(name) {
        const index = getSongs()
            .findIndex(s => s.toLowerCase() === name.toLowerCase());
        if (index !== -1) loadSong(index);
    }

    if (songList) {
        songList.addEventListener("click", e => {
            const title = e.target.closest(".song-title");
            if (!title) return;
            playSongByName(title.textContent.trim());
        });
    }

    // ===============================
    // BUSCADOR DE CANCIONES (filtro en tiempo real)
    // Filtra por nombre dentro de esta playlist. No hace peticiones al servidor.
    // El botón reset restaura la lista completa.
    // ===============================
    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const resetSearch = document.getElementById("resetSearch");

    if (searchForm && searchInput && songList) {
        searchForm.addEventListener("submit", e => {
            e.preventDefault();
            const query = searchInput.value.toLowerCase();
            songList.querySelectorAll(".song-item").forEach(item => {
                const title = item.querySelector(".song-title").textContent.toLowerCase();
                item.style.display = title.includes(query) ? "" : "none";
            });
            updateCounter();
        });
    }

    if (resetSearch) {
        resetSearch.addEventListener("click", () => {
            searchInput.value = "";
            songList.querySelectorAll(".song-item").forEach(i => i.style.display = "");
            updateCounter();
        });
    }

    // ===============================
    // EXPORTAR FUNCIONES GLOBALES
    // ===============================
    window.playPause = playPause;
    window.handleNextClick = handleNextClick;
    window.handlePreviousClick = handlePreviousClick;
    window.toggleShuffle = toggleShuffle;
    window.toggleLoop = toggleLoop;

    // ===============================
    // CONTADOR DE CANCIONES DE LA PLAYLIST
    // Muestra "X canción(es) en esta playlist" (solo canciones visibles tras filtrar).
    // ===============================
    function updateCounter() {
        const footer = document.querySelector(".song-count-footer");
        if (!footer) return;
        const total = songList
            ? songList.querySelectorAll(".song-item:not([style*='display: none']):not([style*='display:none'])").length
            : 0;
        footer.textContent = `${total} canción${total !== 1 ? "es" : ""} en esta playlist`;
    }

    // ===============================
    // ELIMINAR CANCIÓN DE LA PLAYLIST
    // Escucha clics en botones .remove-from-playlist dentro de #songList.
    // Envía la petición al backend y elimina el elemento del DOM si tiene éxito.
    // También actualiza window.songs para mantener sincronizado el array de reproducción.
    // No borra la canción de la biblioteca global, solo la desvincula de esta playlist.
    // ===============================
    if (songList) {
        songList.addEventListener("click", async e => {
            const btn = e.target.closest(".remove-from-playlist");
            if (!btn) return;

            const filename = btn.dataset.filename;
            const playlistId = btn.dataset.playlist;

            try {
                // POST /remove_from_playlist
                const res = await fetch("/remove_from_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename, playlist_id: playlistId })
                });
                const data = await res.json();
                if (data.success) {
                    btn.closest(".song-item")?.remove(); // Elimina del DOM
                    window.songs = (window.songs || []).filter(s => s !== filename); // Actualiza el array global
                    updateCounter();
                } else {
                    alert("Error: " + data.error);
                }
            } catch (err) {
                alert("Error: " + err);
            }
        });
    }

    // ===============================
    // REPRODUCCIÓN AUTOMÁTICA AL TERMINAR
    // Cuando el audio termina, si loop está desactivado pasa automáticamente
    // a la siguiente canción (aleatoria si shuffle está activo, o la siguiente en orden).
    // Si loop está activo, el propio elemento <audio> se encarga de repetir (player.loop = true).
    // ===============================
    if (player) {
        player.addEventListener("ended", () => {
            if (!loop) handleNextClick();
        });
    }

    // ===============================
    // INICIALIZACIÓN
    // ===============================
    if (player && getSongs().length > 0) loadSong(0);
    updateCounter();

    // ===============================
    // SINCRONIZAR PLAYLIST CON YOUTUBE
    // El botón #syncYtBtn envía el ID de la playlist al backend, que compara
    // los vídeos actuales en YouTube con los que hay en la BD y descarga los nuevos.
    // Muestra feedback de estado (#syncStatus) y recarga la página tras el éxito.
    // ===============================
    const syncBtn = document.getElementById("syncYtBtn");
    const syncStatus = document.getElementById("syncStatus");

    if (syncBtn) {
        syncBtn.addEventListener("click", async () => {
            const playlistId = syncBtn.dataset.playlist;

            // Deshabilita el botón y muestra estado de carga
            syncBtn.disabled = true;
            syncBtn.textContent = "Sincronizando...";
            if (syncStatus) {
                syncStatus.style.display = "none";
                syncStatus.className = "sync-status";
            }

            try {
                // POST /sync_youtube_playlist
                const res = await fetch("/sync_youtube_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ playlist_id: playlistId })
                });
                const data = await res.json();

                if (data.success) {
                    if (syncStatus) {
                        syncStatus.textContent = data.message; // Ej: "+3 añadidas, -1 eliminadas"
                        syncStatus.className = "sync-status ok";
                        syncStatus.style.display = "block";
                    }
                    // Recarga tras 1.5s para mostrar los cambios sin que sea abrupto
                    setTimeout(() => location.reload(), 1500);
                } else {
                    if (syncStatus) {
                        syncStatus.textContent = `Error: ${data.error}`;
                        syncStatus.className = "sync-status error";
                        syncStatus.style.display = "block";
                    }
                    // Restaura el botón si hubo error
                    syncBtn.disabled = false;
                    syncBtn.textContent = "Sincronizar con YouTube";
                }
            } catch (err) {
                if (syncStatus) {
                    syncStatus.textContent = `Error de red: ${err}`;
                    syncStatus.className = "sync-status error";
                    syncStatus.style.display = "block";
                }
                syncBtn.disabled = false;
                syncBtn.textContent = "Sincronizar con YouTube";
            }
        });
    }
});
