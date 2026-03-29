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
    function showResults(videos) {

        results.innerHTML = "";

        videos.forEach(video => {

            const li = document.createElement("li");
            li.className = "youtube-video-item";

            const title = document.createElement("span");
            title.textContent = video.title;

            const playBtn = document.createElement("button");
            playBtn.textContent = "▶";
            playBtn.onclick = () => playYoutube(video.url, video.title);

            const downloadBtn = document.createElement("button");
            downloadBtn.textContent = "⬇ Descargar";
            downloadBtn.onclick = () => downloadYoutube(video);

            li.append(title, playBtn, downloadBtn);
            results.appendChild(li);
        });
    }

    // ===============================
    // PLAY YOUTUBE AUDIO
    // ===============================
    async function playYoutube(url, title) {

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

        player.src = data.audio;
        player.play();

        if (nowPlaying)
            nowPlaying.textContent = "Reproduciendo: " + title;
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