// =============================================================================
// player.js — Reproductor principal de la biblioteca de canciones
// Usado en: index.html (página principal)
//
// Responsabilidades:
//   - Menú desplegable de navegación
//   - Reproducir canciones del array global window.songs
//   - Controles: play/pause, siguiente, anterior
//   - Modos: shuffle (aleatorio) y loop (repetición)
//   - Integración con la Media Session API (controles del sistema operativo)
//   - Buscador de canciones en tiempo real (filtro por nombre)
//   - Clic en canción de la lista para reproducirla
//   - Añadir canciones a una playlist (dropdown por canción)
//   - Borrar canción (con confirmación)
//   - Contador de canciones visible en la biblioteca
//
// Datos de entrada:
//   window.songs            → array de nombres de archivo de canciones (inyectado por el HTML)
//   window.currentSongIndex → índice de la canción actualmente cargada (opcional)
//
// Endpoints que consume:
//   GET  /play/<filename>       → stream de audio de la canción
//   POST /add_to_playlist       → añade una canción a una playlist
//   POST /delete_song           → elimina una canción de la biblioteca y del disco
//
// Funciones expuestas globalmente (para botones con onclick en el HTML):
//   window.loadSong(index)
//   window.playPause()
//   window.handleNextClick()
//   window.handlePreviousClick()
//   window.toggleShuffle()
//   window.toggleLoop()
//   window.toggleShuffleUI()   → toggleShuffle + actualiza clase CSS del botón
//   window.toggleLoopUI()      → toggleLoop + actualiza clase CSS del botón
//   window.toggleMenu()
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {

    // ===============================
    // MENÚ DESPLEGABLE DE NAVEGACIÓN
    // ===============================
    window.toggleMenu = function () {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    // Cierra el menú al hacer clic fuera de él
    document.addEventListener("click", function (e) {
        const menu = document.getElementById("dropdownMenu");
        const btn = document.querySelector(".menu-toggle");
        if (!menu || !btn) return;
        if (!menu.contains(e.target) && !btn.contains(e.target)) {
            menu.classList.remove("show");
        }
    });

    // ===============================
    // ACCESO A LA LISTA DE CANCIONES
    // window.songs es un array de nombres de archivo inyectado por el template HTML.
    // getSongs() es un wrapper seguro que devuelve [] si aún no está inicializado.
    // ===============================
    function getSongs() {
        return window.songs || [];
    }

    // Referencias a los elementos del DOM del reproductor
    const player = document.getElementById("player");           // Elemento <audio>
    const audioSource = document.getElementById("audioSource"); // Elemento <source> dentro del <audio>
    const currentSongTitle = document.getElementById("currentSongTitle"); // Texto del título en la UI

    // Estado del reproductor
    let currentSongIndex = window.currentSongIndex || 0;
    let shuffle = false; // Si true, la siguiente canción se elige al azar
    let loop = false;    // Si true, la canción actual se repite al terminar

    // ===============================
    // CARGAR Y REPRODUCIR CANCIÓN
    // Recibe el índice en window.songs, actualiza la fuente del <audio>,
    // lo carga, lo reproduce y actualiza la UI (título + pestaña del navegador).
    // También configura la Media Session API para los controles del SO/auriculares.
    // ===============================
    function loadSong(index) {
        const songs = getSongs();
        if (!songs.length || !player || !audioSource) return;

        // Wrapping circular: si el índice se pasa de los límites, vuelve al otro extremo
        if (index < 0) index = songs.length - 1;
        if (index >= songs.length) index = 0;

        currentSongIndex = index;
        const song = songs[currentSongIndex];

        // Asigna la URL del stream de audio y fuerza la recarga del elemento
        audioSource.src = "/play/" + encodeURIComponent(song);
        player.load();
        player.play().catch(() => {}); // .catch vacío: evita error si el autoplay está bloqueado

        // Actualiza el título visible en la UI y en la pestaña del navegador
        if (currentSongTitle) currentSongTitle.textContent = song;
        document.title = song;

        // Media Session API: permite controlar la reproducción desde el SO,
        // auriculares Bluetooth, pantalla de bloqueo, etc.
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

    // Alterna play/pause según el estado actual del elemento <audio>
    function playPause() {
        if (!player) return;
        player.paused ? player.play() : player.pause();
    }

    // Siguiente canción: si shuffle está activo elige una al azar (distinta a la actual)
    function handleNextClick() {
        const songs = getSongs();
        if (!songs.length) return;

        if (shuffle) {
            let i;
            // Asegura que no se repita la misma canción si hay más de una
            do { i = Math.floor(Math.random() * songs.length); }
            while (i === currentSongIndex && songs.length > 1);
            currentSongIndex = i;
        } else {
            // Avance secuencial con wrapping circular
            currentSongIndex = (currentSongIndex + 1) % songs.length;
        }
        loadSong(currentSongIndex);
    }

    // Canción anterior:
    //   - Si la canción lleva más de 3 segundos → reinicia desde el principio
    //   - Si lleva menos de 3 segundos → va a la canción anterior (o aleatoria con shuffle)
    function handlePreviousClick() {
        const songs = getSongs();
        if (!songs.length || !player) return;

        if (player.currentTime > 3) {
            player.currentTime = 0;
            return;
        }

        if (shuffle) {
            let i;
            do { i = Math.floor(Math.random() * songs.length); }
            while (i === currentSongIndex && songs.length > 1);
            currentSongIndex = i;
        } else {
            currentSongIndex--;
            if (currentSongIndex < 0) currentSongIndex = songs.length - 1;
        }
        loadSong(currentSongIndex);
    }

    // ===============================
    // MODOS: SHUFFLE Y LOOP
    // Las funciones "UI" actualizan también la clase CSS "active" del botón
    // para reflejar visualmente el estado activo/inactivo.
    // ===============================

    // Activa/desactiva el modo aleatorio (lógica pura, sin UI)
    function toggleShuffle() {
        shuffle = !shuffle;
    }

    // Activa/desactiva la repetición (lógica pura, sin UI)
    // También asigna player.loop para que el <audio> repita nativamente
    function toggleLoop() {
        loop = !loop;
        if (player) player.loop = loop;
    }

    // Versión con actualización visual del botón (llamada desde onclick en el HTML)
    window.toggleShuffleUI = function () {
        toggleShuffle();
        const toggle = document.getElementById("shuffleToggle");
        if (toggle) toggle.classList.toggle("active", shuffle);
    };

    window.toggleLoopUI = function () {
        toggleLoop();
        const toggle = document.getElementById("loopToggle");
        if (toggle) toggle.classList.toggle("active", loop);
    };

    // ===============================
    // BUSCADOR DE CANCIONES (filtro en tiempo real)
    // Filtra las canciones visibles en #songList según el texto introducido.
    // No hace ninguna petición al servidor: opera solo sobre el DOM.
    // El botón "X" (resetSearch) borra el filtro y muestra todas de nuevo.
    // ===============================
    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const songList = document.getElementById("songList");
    const resetSearch = document.getElementById("resetSearch");

    if (searchForm && searchInput && songList) {
        searchForm.addEventListener("submit", e => {
            e.preventDefault(); // Evita el envío del formulario al servidor
            const query = searchInput.value.toLowerCase();
            songList.querySelectorAll(".song-item").forEach(item => {
                const title = item.querySelector(".song-title")?.textContent.toLowerCase() || "";
                // Muestra el item si el título contiene la búsqueda, lo oculta si no
                item.style.display = title.includes(query) ? "" : "none";
            });
            updateCounter(); // Actualiza el contador con el número de canciones visibles
        });
    }

    if (resetSearch && songList && searchInput) {
        resetSearch.addEventListener("click", () => {
            searchInput.value = "";
            songList.querySelectorAll(".song-item").forEach(item => item.style.display = "");
            updateCounter();
        });
    }

    // ===============================
    // CLIC EN CANCIÓN DE LA LISTA
    // Escucha clics dentro de #songList y carga la canción cuyo .song-title fue pulsado.
    // Usa event delegation: un solo listener en el contenedor gestiona todos los items.
    // ===============================
    if (songList) {
        songList.addEventListener("click", e => {
            const titleEl = e.target.closest(".song-title");
            if (!titleEl) return;
            // Calcula el índice de la canción dentro de la lista de hijos del songList
            const index = Array.from(songList.children).indexOf(titleEl.closest(".song-item"));
            if (index !== -1) loadSong(index);
        });
    }

    // ===============================
    // AÑADIR CANCIÓN A PLAYLIST
    // Cada canción tiene un wrapper .playlist-wrapper con un botón .add-btn
    // que abre un dropdown con las playlists disponibles.
    // Al hacer clic en una opción del dropdown, se envía la canción al backend.
    // Solo puede haber un dropdown abierto a la vez.
    // ===============================
    document.querySelectorAll(".playlist-wrapper").forEach(wrapper => {
        const btn = wrapper.querySelector(".add-btn");
        const dropdown = wrapper.querySelector(".playlist-dropdown");
        if (!btn || !dropdown) return;

        btn.addEventListener("click", e => {
            e.stopPropagation(); // Evita que el clic cierre el dropdown inmediatamente

            // Cierra cualquier otro dropdown abierto antes de abrir el actual
            document.querySelectorAll(".playlist-dropdown")
                .forEach(d => { if (d !== dropdown) d.classList.remove("show"); });

            dropdown.classList.toggle("show");
        });

        // Cada opción del dropdown representa una playlist
        dropdown.querySelectorAll(".playlist-option").forEach(option => {
            option.addEventListener("click", async () => {
                const playlistId = option.dataset.playlist;
                const songItem = wrapper.closest(".song-item");
                const filename = songItem.dataset.filename;

                try {
                    // POST /add_to_playlist
                    const res = await fetch("/add_to_playlist", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ filename, playlist_id: playlistId })
                    });
                    const data = await res.json();
                    alert(data.success
                        ? `"${filename}" añadida`
                        : `Error: ${data.error}`
                    );
                } catch (err) {
                    alert("Error: " + err);
                }

                dropdown.classList.remove("show"); // Cierra el dropdown tras la acción
            });
        });
    });

    // Cierra todos los dropdowns al hacer clic en cualquier otro sitio de la página
    document.addEventListener("click", () => {
        document.querySelectorAll(".playlist-dropdown")
            .forEach(d => d.classList.remove("show"));
    });

    // ===============================
    // ELIMINAR CANCIÓN
    // Escucha clics en botones .delete-song-btn dentro de #songList.
    // Pide confirmación, envía la petición al backend y elimina el elemento del DOM
    // si el servidor confirma el éxito. También actualiza window.songs y el contador.
    // ===============================
    if (songList) {
        songList.addEventListener("click", async e => {
            if (!e.target.classList.contains("delete-song-btn")) return;
            const btn = e.target;
            const filename = btn.dataset.filename;
            if (!filename) return;

            if (!confirm(`¿Borrar "${filename}"?`)) return;

            try {
                // POST /delete_song
                const res = await fetch("/delete_song", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename })
                });
                const data = await res.json();
                if (data.success) {
                    btn.closest(".song-item")?.remove(); // Elimina el elemento del DOM
                    window.songs = getSongs().filter(s => s !== filename); // Actualiza el array global
                    updateCounter();
                    alert(`"${filename}" borrada correctamente`);
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (err) {
                alert("Error al borrar la canción: " + err);
            }
        });
    }

    // ===============================
    // CONTADOR DE CANCIONES
    // Muestra "X canción(es) en tu biblioteca" en el footer de la lista.
    // Cuenta solo los items visibles (excluye los ocultados por el buscador).
    // ===============================
    function updateCounter() {
        const footer = document.querySelector(".song-count-footer");
        if (!footer) return;
        const total = songList
            ? songList.querySelectorAll(".song-item:not([style*='display: none']):not([style*='display:none'])").length
            : 0;
        footer.textContent = `${total} canción${total !== 1 ? "es" : ""} en tu biblioteca`;
    }

    // ===============================
    // EXPORTAR FUNCIONES GLOBALES
    // Las expone en window para que el HTML pueda llamarlas con onclick="..."
    // y para que otros scripts (ej: youtube.js) puedan acceder al reproductor.
    // ===============================
    window.loadSong = loadSong;
    window.playPause = playPause;
    window.handleNextClick = handleNextClick;
    window.handlePreviousClick = handlePreviousClick;
    window.toggleShuffle = toggleShuffle;
    window.toggleLoop = toggleLoop;

    // ===============================
    // INICIALIZACIÓN
    // Carga la primera canción al arrancar y actualiza el contador inicial.
    // ===============================
    if (player && getSongs().length > 0) loadSong(currentSongIndex);
    updateCounter();
});
