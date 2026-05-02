document.addEventListener("DOMContentLoaded", () => {

    function getSongs() {
        return window.songs || [];
    }

    const player = document.getElementById("player");
    const audioSource = document.getElementById("audioSource");
    const currentSongTitle = document.getElementById("currentSongTitle");
    const songList = document.getElementById("songList");
    const shuffleToggle = document.getElementById("shuffleToggle");
    const shuffleContainer = document.getElementById("shuffleToggleContainer");

    const loopToggle = document.getElementById("loopToggle");
    const loopContainer = document.getElementById("loopToggleContainer");

    let currentSongIndex = 0;
    let shuffle = false;
    let loop = false;

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

        if (shuffle)
            currentSongIndex = Math.floor(Math.random() * songs.length);
        else
            currentSongIndex = (currentSongIndex + 1) % songs.length;

        loadSong(currentSongIndex);
    }

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


    function toggleShuffle() {
        shuffle = !shuffle;
        shuffleToggle?.classList.toggle("active", shuffle);
    }

    function toggleLoop() {
        loop = !loop;
        player.loop = loop; 
        loopToggle?.classList.toggle("active", loop);
    }

    shuffleContainer?.addEventListener("click", toggleShuffle);
    loopContainer?.addEventListener("click", toggleLoop);

    // ===============================
    // CLICK SONG
    // ===============================
    function playSongByName(name) {
        const index = getSongs()
            .findIndex(s => s.toLowerCase() === name.toLowerCase());

        if (index !== -1)
            loadSong(index);
    }

    if (songList) {
        songList.addEventListener("click", e => {

            const title = e.target.closest(".song-title");
            if (!title) return;

            playSongByName(title.textContent.trim());
        });
    }

    // ===============================
    // SEARCH
    // ===============================
    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const resetSearch = document.getElementById("resetSearch");

    if (searchForm && searchInput && songList) {
        searchForm.addEventListener("submit", e => {
            e.preventDefault();

            const query = searchInput.value.toLowerCase();

            songList.querySelectorAll(".song-item").forEach(item => {
                const title = item.querySelector(".song-title")
                    .textContent.toLowerCase();

                item.style.display =
                    title.includes(query) ? "" : "none";
            });
            updateCounter();
        });
    }

    if (resetSearch) {
        resetSearch.addEventListener("click", () => {
            searchInput.value = "";
            songList.querySelectorAll(".song-item")
                .forEach(i => i.style.display = "");
            updateCounter();
        });
    }

    // ===============================
    // EXPORT GLOBAL
    // ===============================
    window.playPause = playPause;
    window.handleNextClick = handleNextClick;
    window.handlePreviousClick = handlePreviousClick;
    window.toggleShuffle = toggleShuffle;
    window.toggleLoop = toggleLoop;

    // ===============================
    // COUNTER
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
    // REMOVE FROM PLAYLIST
    // ===============================
    if (songList) {
        songList.addEventListener("click", async e => {
            const btn = e.target.closest(".remove-from-playlist");
            if (!btn) return;

            const filename = btn.dataset.filename;
            const playlistId = btn.dataset.playlist;

            try {
                const res = await fetch("/remove_from_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename, playlist_id: playlistId })
                });
                const data = await res.json();
                if (data.success) {
                    btn.closest(".song-item")?.remove();
                    window.songs = (window.songs || []).filter(s => s !== filename);
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
    // INITIAL LOAD
    // ===============================
    if (player && getSongs().length > 0)
        loadSong(0);
    updateCounter();

    // ===============================
    // SINCRONIZAR CON YOUTUBE
    // ===============================
    const syncBtn = document.getElementById("syncYtBtn");
    const syncStatus = document.getElementById("syncStatus");

    if (syncBtn) {
        syncBtn.addEventListener("click", async () => {
            const playlistId = syncBtn.dataset.playlist;

            syncBtn.disabled = true;
            syncBtn.textContent = "Sincronizando...";
            if (syncStatus) {
                syncStatus.style.display = "none";
                syncStatus.className = "sync-status";
            }

            try {
                const res = await fetch("/sync_youtube_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ playlist_id: playlistId })
                });
                const data = await res.json();

                if (data.success) {
                    if (syncStatus) {
                        syncStatus.textContent = `${data.message}`;
                        syncStatus.className = "sync-status ok";
                        syncStatus.style.display = "block";
                    }

                    setTimeout(() => location.reload(), 1500);
                } else {
                    if (syncStatus) {
                        syncStatus.textContent = `Error: ${data.error}`;
                        syncStatus.className = "sync-status error";
                        syncStatus.style.display = "block";
                    }
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