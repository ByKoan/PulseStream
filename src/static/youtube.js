document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("youtube-search-input");
    const btn = document.getElementById("youtube-search-btn");
    const results = document.getElementById("youtube-results");
    const player = document.getElementById("youtube-player");
    const nowPlaying = document.getElementById("now-playing");

    const loopToggle = document.getElementById("youtubeLoopToggle");
    const loopContainer = document.getElementById("youtubeLoopToggleContainer");

    const songList = document.getElementById("songList");

    let loopSong = false;

    // ===============================
    // MENU DROPDOWN
    // ===============================
    window.toggleMenu = function () {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    document.addEventListener("click", function(e) {
        const menu = document.getElementById("dropdownMenu");
        const btn = document.querySelector(".menu-toggle");

        if (!menu || !btn) return;

        if (!menu.contains(e.target) && !btn.contains(e.target)) {
            menu.classList.remove("show");
        }
    });

    // ===============================
    // LOOP
    // ===============================
    function toggleLoopUI() {

        loopSong = !loopSong;

        if (loopToggle) {
            loopToggle.classList.toggle("active", loopSong);
        }
    }

    if (loopContainer) {
        loopContainer.addEventListener("click", toggleLoopUI);
    }

    if (player) {
        player.addEventListener("ended", () => {
            if (loopSong) {
                player.currentTime = 0;
                player.play();
            }
        });
    }

    // ===============================
    // SEARCH
    // ===============================
    async function searchYoutube() {

        const query = input.value.trim();
        if (!query) return;

        const res = await fetch("/youtube_search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query })
        });

        const data = await res.json();

        if (!data.success) {
            alert(data.error);
            return;
        }

        showResults(data.results);
    }

    // ===============================
    // SHOW RESULTS
    // ===============================

    function extractId(url) {
        const match = url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
        return match ? match[1] : null;
    }

    function showResults(videos) {

        results.innerHTML = "";

        videos.forEach(video => {

            const li = document.createElement("li");
            li.className = "youtube-video-item";

            // ===== THUMBNAIL (VIDEO) =====
            const img = document.createElement("img");
            const videoId = extractId(video.url);

            img.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
            img.className = "yt-thumb";

            // click = VIDEO
            img.onclick = () => playYoutubeVideo(video.url, video.title);

            // ===== TITLE =====
            const title = document.createElement("span");
            title.textContent = video.title;
            title.className = "youtube-video-title";

            // ===== BOTÓN AUDIO (YA EXISTENTE) =====
            const playBtn = document.createElement("button");
            playBtn.textContent = "▶ Audio";
            playBtn.onclick = () => playYoutube(video.url, video.title);

            // ===== DESCARGA (YA EXISTENTE) =====
            const downloadBtn = document.createElement("button");
            downloadBtn.textContent = "⬇ Descargar";
            downloadBtn.onclick = () => downloadYoutube(video);

            // ===== CONTENEDOR DERECHA =====
            const actions = document.createElement("div");
            actions.className = "youtube-actions";
            actions.style.gap = "8px";

            actions.append(playBtn, downloadBtn);

            // ===== ESTRUCTURA FINAL =====
            li.append(img, title, actions);
            results.appendChild(li);
        });
    }

    // ===============================
    // PLAY YOUTUBE AUDIO
    // ===============================
    async function playYoutube(url, title) {
        try {
            // Solicitud al servidor para obtener el audio
            const res = await fetch("/youtube_audio", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            const data = await res.json();

            if (!data.success) {
                alert(data.error);
                return;
            }

            // Reproducir el audio
            player.src = data.audio;
            player.play();

            // Actualizar texto en la interfaz
            if (nowPlaying)
                nowPlaying.textContent = "Reproduciendo: " + title;

            // =========================
            // Media Session API
            // =========================
            if ("mediaSession" in navigator) {
                navigator.mediaSession.metadata = new MediaMetadata({
                    title: title,
                    artist: "Koan",
                    album: "MusicCloudServer",
                    artwork: [
                        { src: "https://via.placeholder.com/96", sizes: "96x96", type: "image/png" }
                    ]
                });

                navigator.mediaSession.setActionHandler("play", () => player.play());
                navigator.mediaSession.setActionHandler("pause", () => player.pause());
                navigator.mediaSession.setActionHandler("nexttrack", handleNextClick);
                navigator.mediaSession.setActionHandler("previoustrack", handlePreviousClick);
            }

        } catch (error) {
            console.error("Error al reproducir YouTube:", error);
        }
    }

    // ===============================
    // PLAY YOUTUBE VIDEO
    // ===============================

    async function playYoutubeVideo(url, title) {

        const player = document.getElementById("youtube-player");

        try {
            const res = await fetch("/youtube_video", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            const data = await res.json();

            console.log("VIDEO RESPONSE:", data);

            if (!data.success) {
                alert(data.error);
                return;
            }

            // MOSTRAR REPRODUCTOR
            player.style.display = "block";

            // RESET COMPLETO (CLAVE)
            player.pause();
            player.removeAttribute("src");
            player.load();

            // asignar nuevo stream
            player.src = data.stream;

            // forzar carga
            player.load();

            const playPromise = player.play();

            if (playPromise !== undefined) {
                playPromise.catch(err => {
                    console.error("Autoplay bloqueado:", err);
                });
            }

            document.getElementById("now-playing").textContent =
                "Reproduciendo: " + title;

        } catch (err) {
            console.error("ERROR VIDEO:", err);
        }
    }

    // ===============================
    // DOWNLOAD + AUTO ADD
    // ===============================
    async function downloadYoutube(video) {

        const res = await fetch("/youtube_download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: video.url })
        });

        const data = await res.json();

        if (!data.success) {
            alert(data.error);
            return;
        }

        alert(`"${data.filename}" descargada`);

        // asegurar array global
        if (!window.songs) window.songs = [];

        const newIndex = window.songs.length;
        window.songs.push(data.filename);

        // añadir a UI
        if (songList) {

            const li = document.createElement("li");
            li.className = "song-item";
            li.dataset.filename = data.filename;

            li.innerHTML = `
                <span class="song-title">${data.filename}</span>
            `;

            li.querySelector(".song-title")
                .addEventListener("click", () => {
                    if (window.loadSong)
                        window.loadSong(newIndex);
                });

            songList.appendChild(li);
        }

        // guardar en DB
        await fetch("/add_song_to_db", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                filename: data.filename,
                title: video.title
            })
        });

        // AUTO PLAY 🔥
        if (window.loadSong)
            window.loadSong(newIndex);
    }

    // ===============================
    // EVENTS
    // ===============================
    if (btn) btn.addEventListener("click", searchYoutube);

    if (input) {
        input.addEventListener("keypress", e => {
            if (e.key === "Enter") searchYoutube();
        });
    }

});