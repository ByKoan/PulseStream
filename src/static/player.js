document.addEventListener("DOMContentLoaded", () => {

    // ===============================
    // SONG ACCESS
    // ===============================
    function getSongs() {
        return window.songs || [];
    }

    const player = document.getElementById("player");
    const audioSource = document.getElementById("audioSource");
    const currentSongTitle = document.getElementById("currentSongTitle");

    let currentSongIndex = window.currentSongIndex || 0;
    let shuffle = false;
    let loop = false;

    // ===============================
    // LOAD SONG
    // ===============================
    function loadSong(index) {
        const songs = getSongs();
        if (!songs.length || !player || !audioSource) return;

        if (index < 0) index = songs.length - 1;
        if (index >= songs.length) index = 0;

        currentSongIndex = index;
        const song = songs[currentSongIndex];

        audioSource.src = "/play/" + encodeURIComponent(song);
        player.load();
        player.play().catch(() => {});

        if (currentSongTitle) currentSongTitle.textContent = song;
        document.title = song;

        // Media Session API
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
    // CONTROLS
    // ===============================
    function playPause() {
        if (!player) return;
        player.paused ? player.play() : player.pause();
    }

    function handleNextClick() {
        const songs = getSongs();
        if (!songs.length) return;

        if (shuffle) {
            let i;
            do { i = Math.floor(Math.random() * songs.length); } 
            while (i === currentSongIndex && songs.length > 1);
            currentSongIndex = i;
        } else {
            currentSongIndex = (currentSongIndex + 1) % songs.length;
        }
        loadSong(currentSongIndex);
    }

    function handlePreviousClick() {
        const songs = getSongs();
        if (!songs.length || !player) return;

        if (player.currentTime > 3) { player.currentTime = 0; return; }

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

    function toggleShuffle() {
        shuffle = !shuffle;
        const el = document.getElementById("shuffleStatus");
        if (el) el.textContent = shuffle ? "Activado" : "Desactivado";
    }

    function toggleLoop() {
        loop = !loop;
        if (player) player.loop = loop;
        const el = document.getElementById("loopStatus");
        if (el) el.textContent = loop ? "Activado" : "Desactivado";
    }

    // ===============================
    // SEARCH
    // ===============================
    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const songList = document.getElementById("songList");
    const resetSearch = document.getElementById("resetSearch");

    if (searchForm && searchInput && songList) {
        searchForm.addEventListener("submit", e => {
            e.preventDefault();
            const query = searchInput.value.toLowerCase();
            songList.querySelectorAll(".song-item").forEach(item => {
                const title = item.querySelector(".song-title")?.textContent.toLowerCase() || "";
                item.style.display = title.includes(query) ? "" : "none";
            });
        });
    }

    if (resetSearch && songList && searchInput) {
        resetSearch.addEventListener("click", () => {
            searchInput.value = "";
            songList.querySelectorAll(".song-item").forEach(item => item.style.display = "");
        });
    }

    // ===============================
    // CLICK SONG
    // ===============================
    if (songList) {
        songList.addEventListener("click", e => {
            const titleEl = e.target.closest(".song-title");
            if (!titleEl) return;
            const index = Array.from(songList.children).indexOf(titleEl.closest(".song-item"));
            if (index !== -1) loadSong(index);
        });
    }

    // ===============================
    // ADD TO PLAYLIST
    // ===============================
    document.querySelectorAll(".add-to-playlist").forEach(container => {
        const addBtn = container.querySelector(".add-btn");
        const select = container.querySelector(".playlist-select");
        if (!addBtn || !select) return;

        addBtn.addEventListener("click", e => {
            e.stopPropagation();
            const isOpen = select.style.display === "inline-block";
            document.querySelectorAll(".playlist-select").forEach(s => s.style.display = "none");
            select.style.display = isOpen ? "none" : "inline-block";
        });

        select.addEventListener("click", e => e.stopPropagation());

        select.addEventListener("change", async () => {
            const playlistId = select.value;
            if (!playlistId) return;
            const songItem = container.closest(".song-item");
            const filename = songItem?.dataset.filename;
            if (!filename) return;

            try {
                const res = await fetch("/add_to_playlist", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ filename, playlist_id: playlistId })
                });
                const data = await res.json();
                alert(data.success ? `"${filename}" añadida a la playlist` : `Error: ${data.error}`);
            } catch (err) {
                alert("Error al añadir la canción: " + err);
            }

            select.style.display = "none";
            select.selectedIndex = 0;
        });
    });

    document.addEventListener("click", () => {
        document.querySelectorAll(".playlist-select").forEach(s => s.style.display = "none");
    });

    // ===============================
    // DELETE SONG
    // ===============================
    if (songList) {
        songList.addEventListener("click", async e => {
            if (!e.target.classList.contains("delete-song-btn")) return;
            const btn = e.target;
            const filename = btn.dataset.filename;
            if (!filename) return;

            if (!confirm(`¿Borrar "${filename}"?`)) return;

            try {
                const res = await fetch("/delete_song", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ filename })
                });
                const data = await res.json();
                if (data.success) {
                    btn.closest(".song-item")?.remove();
                    window.songs = getSongs().filter(s => s !== filename);
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
    // EXPORT FUNCTIONS
    // ===============================
    window.loadSong = loadSong;
    window.playPause = playPause;
    window.handleNextClick = handleNextClick;
    window.handlePreviousClick = handlePreviousClick;
    window.toggleShuffle = toggleShuffle;
    window.toggleLoop = toggleLoop;

    // ===============================
    // INITIAL LOAD
    // ===============================
    if (player && getSongs().length > 0) loadSong(currentSongIndex);

});