// =============================================================================
// youtube.js — Buscador y reproductor de YouTube
// Usado en: youtube.html
//
// Responsabilidades:
//   - Menú desplegable de navegación
//   - Buscar vídeos en YouTube por texto o pulsando Enter
//   - Mostrar resultados con miniatura, título y botones de acción
//   - Reproducir el audio de un vídeo de YouTube en streaming (sin descargar)
//   - Reproducir el vídeo de YouTube en streaming (sin descargar)
//   - Modo loop: repite el audio o vídeo al terminar
//   - Descargar un vídeo como MP3 a la biblioteca del usuario
//   - Registrar la canción descargada en la BD (/add_song_to_db)
//   - Añadir la canción descargada a la lista de reproducción sin recargar
//   - Contador de resultados de búsqueda
//
// Endpoints que consume:
//   POST /youtube_search    → busca vídeos en YouTube, devuelve título + URL
//   POST /youtube_audio     → obtiene URL de streaming de audio de un vídeo
//   POST /youtube_video     → obtiene URL de streaming de vídeo (mp4)
//   POST /youtube_download  → descarga el vídeo como MP3 al servidor
//   POST /add_song_to_db    → registra la canción descargada en la BD
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {

    // Referencias a los elementos del DOM
    const input = document.getElementById("youtube-search-input");     // Campo de búsqueda
    const btn = document.getElementById("youtube-search-btn");         // Botón "Buscar"
    const results = document.getElementById("youtube-results");        // Lista de resultados
    const audioPlayer = document.getElementById("youtube-audio-player"); // <audio> para streaming
    const videoPlayer = document.getElementById("youtube-video-player"); // <video> para streaming
    const nowPlaying = document.getElementById("now-playing");          // Texto "Reproduciendo: X"
    const loopToggle = document.getElementById("youtubeLoopToggle");    // Icono del botón loop
    const loopContainer = document.getElementById("youtubeLoopToggleContainer"); // Botón loop completo
    const songList = document.getElementById("songList");               // Lista de canciones descargadas

    // Estado del modo loop (comparte estado entre audio y vídeo)
    let loopSong = false;

    // ===============================
    // MENÚ DESPLEGABLE DE NAVEGACIÓN
    // ===============================
    window.toggleMenu = function () {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    document.addEventListener("click", function (e) {
        const menu = document.getElementById("dropdownMenu");
        const toggle = document.querySelector(".menu-toggle");
        if (!menu || !toggle) return;
        if (!menu.contains(e.target) && !toggle.contains(e.target)) {
            menu.classList.remove("show");
        }
    });

    // ===============================
    // MODO LOOP
    // Alterna el estado de repetición y actualiza la clase CSS del botón.
    // Cuando un audio o vídeo termina, lo reinicia desde el principio si loop está activo.
    // ===============================
    function toggleLoopUI() {
        loopSong = !loopSong;
        if (loopToggle) loopToggle.classList.toggle("active", loopSong);
    }

    if (loopContainer) loopContainer.addEventListener("click", toggleLoopUI);

    // Reinicia el audio al terminar si loop está activo
    if (audioPlayer) {
        audioPlayer.addEventListener("ended", () => {
            if (loopSong) { audioPlayer.currentTime = 0; audioPlayer.play(); }
        });
    }

    // Reinicia el vídeo al terminar si loop está activo
    if (videoPlayer) {
        videoPlayer.addEventListener("ended", () => {
            if (loopSong) { videoPlayer.currentTime = 0; videoPlayer.play(); }
        });
    }

    // ===============================
    // CONTADOR DE RESULTADOS DE BÚSQUEDA
    // Muestra "X resultado(s) encontrado(s)" en el footer de la lista.
    // Se oculta si no hay resultados y se muestra cuando los hay.
    // ===============================
    function updateCounter() {
        const footer = document.getElementById("youtube-count-footer");
        const countEl = document.getElementById("youtube-result-count");
        const plural1 = document.getElementById("youtube-result-plural");
        const plural2 = document.getElementById("youtube-result-plural2");
        if (!footer || !countEl) return;

        const total = document.getElementById("youtube-results")
            ?.querySelectorAll(".youtube-video-item").length || 0;

        countEl.textContent = total;
        const s = total === 1 ? "" : "s"; // Pluralización
        if (plural1) plural1.textContent = s;
        if (plural2) plural2.textContent = s;
        footer.style.display = total > 0 ? "block" : "none"; // Oculta si no hay resultados
    }

    // ===============================
    // BÚSQUEDA DE VÍDEOS EN YOUTUBE
    // Envía el texto del input al backend, que usa yt-dlp para buscar en YouTube
    // y devuelve los 10 primeros resultados con título y URL.
    // ===============================
    async function searchYoutube() {
        const query = input.value.trim();
        if (!query) return;

        btn.textContent = "Buscando...";
        btn.disabled = true;

        try {
            // POST /youtube_search
            const res = await fetch("/youtube_search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });
            const data = await res.json();
            if (!data.success) { alert(data.error); return; }
            showResults(data.results); // Renderiza los resultados en el DOM
        } catch (err) {
            alert("Error al buscar: " + err);
        } finally {
            btn.textContent = "Buscar";
            btn.disabled = false;
        }
    }

    // ===============================
    // MOSTRAR RESULTADOS DE BÚSQUEDA
    // Para cada vídeo crea un elemento <li> con:
    //   - Miniatura (img) → clic reproduce el vídeo en streaming
    //   - Título del vídeo
    //   - Botón "Reproducir Audio" → reproduce solo el audio en streaming
    //   - Botón "⬇" → descarga el vídeo como MP3 a la biblioteca
    // Llama a updateCounter() al finalizar para actualizar el footer.
    // ===============================

    // Extrae el ID de YouTube de una URL (ej: "dQw4w9WgXcQ" de "youtube.com/watch?v=dQw4w9WgXcQ")
    function extractId(url) {
        const match = url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
        return match ? match[1] : null;
    }

    function showResults(videos) {
        results.innerHTML = ""; // Limpia resultados anteriores

        videos.forEach(video => {
            const li = document.createElement("li");
            li.className = "youtube-video-item";

            const videoId = extractId(video.url);

            // Miniatura: usa la imagen de YouTube por ID del vídeo
            const img = document.createElement("img");
            img.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
            img.className = "yt-thumb";
            img.title = "Click para reproducir video";
            img.onclick = () => playYoutubeVideo(video.url, video.title); // Clic → reproduce vídeo

            // Título
            const title = document.createElement("span");
            title.textContent = video.title;
            title.className = "youtube-video-title";

            // Botón para reproducir solo el audio en streaming
            const playBtn = document.createElement("button");
            playBtn.textContent = "Reproducir Audio";
            playBtn.className = "yt-red-btn";
            playBtn.onclick = () => playYoutubeAudio(video.url, video.title);

            // Botón para descargar como MP3
            const downloadBtn = document.createElement("button");
            downloadBtn.textContent = "⬇";
            playBtn.className = "yt-red-btn"; // Nota: esto sobreescribe la clase de playBtn (bug existente)
            downloadBtn.onclick = () => downloadYoutube(video);

            const actions = document.createElement("div");
            actions.className = "youtube-actions";
            actions.style.gap = "8px";
            actions.append(playBtn, downloadBtn);

            li.append(img, title, actions);
            results.appendChild(li);
        });

        updateCounter(); // Actualiza el contador con el número de resultados mostrados
    }

    // ===============================
    // REPRODUCIR AUDIO EN STREAMING
    // Solicita al backend la URL directa de audio del vídeo.
    // Detiene el vídeo si estaba activo, oculta el <video> y muestra el <audio>.
    // Actualiza el texto "Reproduciendo" y configura la Media Session API.
    // ===============================
    async function playYoutubeAudio(url, title) {
        try {
            nowPlaying.textContent = "Cargando audio...";

            // POST /youtube_audio → devuelve la URL directa del stream de audio
            const res = await fetch("/youtube_audio", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });
            const data = await res.json();
            if (!data.success) {
                alert(data.error);
                nowPlaying.textContent = "Error al cargar";
                return;
            }

            // Detiene el reproductor de vídeo y lo oculta
            videoPlayer.pause();
            videoPlayer.removeAttribute("src");
            videoPlayer.load();
            videoPlayer.style.display = "none";

            // Muestra el reproductor de audio y lo lanza
            audioPlayer.style.display = "block";
            audioPlayer.src = data.audio; // URL directa del stream de audio
            audioPlayer.play();

            nowPlaying.textContent = "Reproduciendo: " + title;

            // Integración con controles del SO (auriculares, pantalla de bloqueo, etc.)
            if ("mediaSession" in navigator) {
                navigator.mediaSession.metadata = new MediaMetadata({ title });
                navigator.mediaSession.setActionHandler("play", () => audioPlayer.play());
                navigator.mediaSession.setActionHandler("pause", () => audioPlayer.pause());
            }
        } catch (err) {
            console.error("Error al reproducir audio:", err);
        }
    }

    // ===============================
    // REPRODUCIR VÍDEO EN STREAMING
    // Solicita al backend la URL directa del stream de vídeo (preferiblemente mp4).
    // El backend itera los formatos disponibles y elige el primero con audio+vídeo.
    // Detiene el audio si estaba activo, oculta el <audio> y muestra el <video>.
    // ===============================
    async function playYoutubeVideo(url, title) {
        try {
            nowPlaying.textContent = "Cargando video...";

            // POST /youtube_video → devuelve la URL directa del stream con audio y vídeo
            const res = await fetch("/youtube_video", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });
            const data = await res.json();
            if (!data.success) {
                alert(data.error);
                nowPlaying.textContent = "Error al cargar";
                return;
            }

            // Detiene el reproductor de audio y lo oculta
            audioPlayer.pause();
            audioPlayer.removeAttribute("src");
            audioPlayer.load();
            audioPlayer.style.display = "none";

            // Muestra el reproductor de vídeo
            videoPlayer.style.display = "block";

            // Resetea el vídeo antes de asignar la nueva fuente (evita glitches)
            videoPlayer.pause();
            videoPlayer.removeAttribute("src");
            videoPlayer.load();
            videoPlayer.src = data.stream; // URL directa del stream de vídeo
            videoPlayer.load();

            // Intenta reproducir (puede ser rechazado por política de autoplay del navegador)
            const p = videoPlayer.play();
            if (p) p.catch(err => console.error("Autoplay bloqueado:", err));

            nowPlaying.textContent = "Reproduciendo: " + title;
        } catch (err) {
            console.error("Error al reproducir video:", err);
        }
    }

    // ===============================
    // DESCARGAR VÍDEO COMO MP3
    // Envía la URL al backend, que descarga el audio en MP3 y lo guarda en la carpeta
    // del usuario. Tras la descarga:
    //   1. Añade la canción al array window.songs
    //   2. Añade un elemento a la lista #songList del DOM (para reproducirla sin recargar)
    //   3. Llama a /add_song_to_db para asegurarse de que está en la BD
    //   4. Carga la canción en el reproductor principal (si window.loadSong existe)
    // ===============================
    async function downloadYoutube(video) {
        // POST /youtube_download — puede tardar según el tamaño del vídeo
        const res = await fetch("/youtube_download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: video.url })
        });
        const data = await res.json();
        if (!data.success) { alert(data.error); return; }

        alert(`"${data.filename}" descargada`);

        // Añade la canción al array global de canciones del reproductor
        if (!window.songs) window.songs = [];
        const newIndex = window.songs.length;
        window.songs.push(data.filename);

        // Añade la canción a la lista visible #songList sin recargar la página
        if (songList) {
            const li = document.createElement("li");
            li.className = "song-item";
            li.dataset.filename = data.filename;
            li.innerHTML = `<span class="song-title">${data.filename}</span>`;
            // Al hacer clic en el título → la carga en el reproductor principal
            li.querySelector(".song-title").addEventListener("click", () => {
                if (window.loadSong) window.loadSong(newIndex);
            });
            songList.appendChild(li);
        }

        // Carga y reproduce la canción recién descargada en el reproductor principal
        if (window.loadSong) window.loadSong(newIndex);
    }

    // ===============================
    // EVENTOS: BÚSQUEDA
    // Dispara la búsqueda tanto al pulsar el botón como al presionar Enter en el input.
    // ===============================
    if (btn) btn.addEventListener("click", searchYoutube);
    if (input) input.addEventListener("keypress", e => {
        if (e.key === "Enter") searchYoutube();
    });
});
