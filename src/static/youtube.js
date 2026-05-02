document.addEventListener("DOMContentLoaded", () => {

    const input         = document.getElementById("youtube-search-input");
    const btn           = document.getElementById("youtube-search-btn");
    const results       = document.getElementById("youtube-results");
    const audioPlayer   = document.getElementById("youtube-audio-player");
    const videoPlayer   = document.getElementById("youtube-video-player");
    const nowPlaying    = document.getElementById("now-playing");
    const loopToggle    = document.getElementById("youtubeLoopToggle");
    const loopContainer = document.getElementById("youtubeLoopToggleContainer");
    const songList      = document.getElementById("songList");

    let loopSong = false;

    // ===============================
    // MENU DROPDOWN
    // ===============================
    window.toggleMenu = function () {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    document.addEventListener("click", function(e) {
        const menu   = document.getElementById("dropdownMenu");
        const toggle = document.querySelector(".menu-toggle");
        if (!menu || !toggle) return;
        if (!menu.contains(e.target) && !toggle.contains(e.target)) {
            menu.classList.remove("show");
        }
    });

    // ===============================
    // LOOP
    // ===============================
    function toggleLoopUI() {
        loopSong = !loopSong;
        if (loopToggle) loopToggle.classList.toggle("active", loopSong);
    }

    if (loopContainer) loopContainer.addEventListener("click", toggleLoopUI);

    if (audioPlayer) {
        audioPlayer.addEventListener("ended", () => {
            if (loopSong) { audioPlayer.currentTime = 0; audioPlayer.play(); }
        });
    }
    if (videoPlayer) {
        videoPlayer.addEventListener("ended", () => {
            if (loopSong) { videoPlayer.currentTime = 0; videoPlayer.play(); }
        });
    }

    // ===============================
    // COUNTER
    // ===============================
    function updateCounter() {
        const footer  = document.getElementById("youtube-count-footer");
        const countEl = document.getElementById("youtube-result-count");
        const plural1 = document.getElementById("youtube-result-plural");
        const plural2 = document.getElementById("youtube-result-plural2");
        if (!footer || !countEl) return;
        const total = document.getElementById("youtube-results")
            ?.querySelectorAll(".youtube-video-item").length || 0;
        countEl.textContent = total;
        const s = total === 1 ? "" : "s";
        if (plural1) plural1.textContent = s;
        if (plural2) plural2.textContent = s;
        footer.style.display = total > 0 ? "block" : "none";
    }

    // ===============================
    // SEARCH
    // ===============================
    async function searchYoutube() {
        const query = input.value.trim();
        if (!query) return;

        btn.textContent = "Buscando...";
        btn.disabled = true;

        try {
            const res = await fetch("/youtube_search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });
            const data = await res.json();
            if (!data.success) { alert(data.error); return; }
            showResults(data.results);
        } catch (err) {
            alert("Error al buscar: " + err);
        } finally {
            btn.textContent = "Buscar";
            btn.disabled = false;
        }
    }

    // ===============================
    // SHOW RESULTS + CONTADOR
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

            const videoId = extractId(video.url);

            // Miniatura → reproduce video
            const img = document.createElement("img");
            img.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
            img.className = "yt-thumb";
            img.title = "Click para reproducir video";
            img.onclick = () => playYoutubeVideo(video.url, video.title);

            // Título
            const title = document.createElement("span");
            title.textContent = video.title;
            title.className = "youtube-video-title";

            // Botón audio
            const playBtn = document.createElement("button");
            playBtn.textContent = "Reproducir Audio";
            playBtn.className = "yt-red-btn";
            playBtn.onclick = () => playYoutubeAudio(video.url, video.title);

            // Botón descarga
            const downloadBtn = document.createElement("button");
            downloadBtn.textContent = "⬇";
            playBtn.className = "yt-red-btn";
            downloadBtn.onclick = () => downloadYoutube(video);

            const actions = document.createElement("div");
            actions.className = "youtube-actions";
            actions.style.gap = "8px";
            actions.append(playBtn, downloadBtn);

            li.append(img, title, actions);
            results.appendChild(li);
        });

        updateCounter();
    }

    // ===============================
    // PLAY AUDIO
    // ===============================
    async function playYoutubeAudio(url, title) {
        try {
            nowPlaying.textContent = "Cargando audio...";

            const res = await fetch("/youtube_audio", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });
            const data = await res.json();
            if (!data.success) { alert(data.error); nowPlaying.textContent = "Error al cargar"; return; }

            // Parar video y mostrar audio
            videoPlayer.pause();
            videoPlayer.removeAttribute("src");
            videoPlayer.load();
            videoPlayer.style.display = "none";
            audioPlayer.style.display = "block";

            audioPlayer.src = data.audio;
            audioPlayer.play();

            nowPlaying.textContent = "Reproduciendo: " + title;

            if ("mediaSession" in navigator) {
                navigator.mediaSession.metadata = new MediaMetadata({ title });
                navigator.mediaSession.setActionHandler("play",  () => audioPlayer.play());
                navigator.mediaSession.setActionHandler("pause", () => audioPlayer.pause());
            }
        } catch (err) {
            console.error("Error al reproducir audio:", err);
        }
    }

    // ===============================
    // PLAY VIDEO
    // ===============================
    async function playYoutubeVideo(url, title) {
        try {
            nowPlaying.textContent = "Cargando video...";

            const res = await fetch("/youtube_video", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });
            const data = await res.json();
            if (!data.success) { alert(data.error); nowPlaying.textContent = "Error al cargar"; return; }

            // Parar audio y mostrar video
            audioPlayer.pause();
            audioPlayer.removeAttribute("src");
            audioPlayer.load();
            audioPlayer.style.display = "none";
            videoPlayer.style.display = "block";

            videoPlayer.pause();
            videoPlayer.removeAttribute("src");
            videoPlayer.load();
            videoPlayer.src = data.stream;
            videoPlayer.load();

            const p = videoPlayer.play();
            if (p) p.catch(err => console.error("Autoplay bloqueado:", err));

            nowPlaying.textContent = "Reproduciendo: " + title;
        } catch (err) {
            console.error("Error al reproducir video:", err);
        }
    }

    // ===============================
    // DOWNLOAD
    // ===============================
    async function downloadYoutube(video) {
        const res = await fetch("/youtube_download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: video.url })
        });
        const data = await res.json();
        if (!data.success) { alert(data.error); return; }

        alert(`"${data.filename}" descargada`);

        if (!window.songs) window.songs = [];
        const newIndex = window.songs.length;
        window.songs.push(data.filename);

        if (songList) {
            const li = document.createElement("li");
            li.className = "song-item";
            li.dataset.filename = data.filename;
            li.innerHTML = `<span class="song-title">${data.filename}</span>`;
            li.querySelector(".song-title").addEventListener("click", () => {
                if (window.loadSong) window.loadSong(newIndex);
            });
            songList.appendChild(li);
        }

        await fetch("/add_song_to_db", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: data.filename, title: video.title })
        });

        if (window.loadSong) window.loadSong(newIndex);
    }

    // ===============================
    // EVENTS
    // ===============================
    if (btn) btn.addEventListener("click", searchYoutube);
    if (input) input.addEventListener("keypress", e => {
        if (e.key === "Enter") searchYoutube();
    });

});
