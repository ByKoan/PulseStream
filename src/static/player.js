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
            do {
                i = Math.floor(Math.random() * songs.length);
            } while (i === currentSongIndex && songs.length > 1);
            currentSongIndex = i;
        } else {
            currentSongIndex = (currentSongIndex + 1) % songs.length;
        }

        loadSong(currentSongIndex);
    }

    function handlePreviousClick() {
        const songs = getSongs();
        if (!songs.length || !player) return;

        if (player.currentTime > 3) {
            player.currentTime = 0;
            return;
        }

        if (shuffle) {
            let i;
            do {
                i = Math.floor(Math.random() * songs.length);
            } while (i === currentSongIndex && songs.length > 1);
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
            const items = songList.querySelectorAll(".song-item");
            items.forEach(item => {
                const title = item.querySelector(".song-title")?.textContent.toLowerCase() || "";
                item.style.display = title.includes(query) ? "" : "none";
            });
            const firstVisible = songList.querySelector(".song-item:not([style*='display: none']) .song-title");
            if (firstVisible) window.playSongByName(firstVisible.textContent);
        });
    }

    if (resetSearch && songList && searchInput) {
        resetSearch.addEventListener("click", () => {
            searchInput.value = "";
            songList.querySelectorAll(".song-item").forEach(item => item.style.display = "");
        });
    }

    // ===============================
    // PLAYLIST ADD
    // ===============================
    document.querySelectorAll(".add-to-playlist").forEach(container => {
        const addBtn = container.querySelector(".add-btn");
        const select = container.querySelector(".playlist-select");
        if (!addBtn || !select) return;

        addBtn.addEventListener("click", e => {
            e.stopPropagation();
            const isOpen = select.style.display === "inline-block";
            document.querySelectorAll(".playlist-select").forEach(s => s.style.display = "none");
            if (!isOpen) select.style.display = "inline-block";
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
                    headers: { "Content-Type": "application/json" },
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
                    headers: { "Content-Type": "application/json" },
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
                alert(`Error al borrar la canción: ${err}`);
            }
        });
    }

    // ===============================
    // BAN INLINE
    // ===============================
    document.querySelectorAll(".ban").forEach(btn => {
        btn.addEventListener("click", () => {
            const form = btn.closest("form");
            const input = form?.querySelector(".ban-hours-input");
            if (!input) return;

            if (input.style.display === "none") {
                input.style.display = "inline-block";
                input.focus();
            } else {
                if (!input.value || Number(input.value) <= 0) {
                    alert("Introduce un número válido de horas");
                    input.focus();
                    return;
                }
                form.submit();
            }
        });
    });

    // ===============================
    // CHANGE PASSWORD INLINE
    // ===============================
    document.addEventListener("click", e => {
        if (!e.target.classList.contains("change-password-btn")) return;
        const form = e.target.closest("form");
        const input = form?.querySelector(".password-input");
        if (!input) return;

        if (!input.style.display || input.style.display === "none") {
            input.style.display = "inline-block";
            input.focus();
        } else {
            if (!input.value.trim()) {
                alert("Introduce una contraseña válida");
                input.focus();
                return;
            }
            form.submit();
        }
    });

    // ===============================
    // SELECT ROLE INLINE
    // ===============================
    document.querySelectorAll(".role-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const form = btn.closest(".role-form");
            const select = form?.querySelector(".role-select");
            if (!select) return;

            if (!select.style.display || select.style.display === "none") {
                select.style.display = "inline-block";
                select.focus();
            } else {
                if (!select.value) {
                    alert("Selecciona un rol válido");
                    select.focus();
                    return;
                }
                form.submit();
            }
        });
    });

    document.querySelectorAll(".role-select").forEach(select => {
        select.addEventListener("click", e => e.stopPropagation());
    });

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
                input.value = nameEl.textContent;
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
    // SYSTEM STATS CHARTS
    // ===============================
    if (window.systemStats) {
        const createChart = (id, value, color) => new Chart(document.getElementById(id), {
            type: "doughnut",
            data: { datasets: [{ data: [value, 100 - value], backgroundColor: [color, "#333"] }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });

        const cpuChart = createChart("cpuChart", window.systemStats.cpu, "#ff6384");
        const ramChart = createChart("ramChart", window.systemStats.ram_percent, "#36a2eb");
        const diskChart = createChart("diskChart", window.systemStats.disk_percent, "#ffce56");
        const netUpChart = createChart("netUpChart", 0, "#4bc0c0");
        const netDownChart = createChart("netDownChart", 0, "#ff9f40");

        let lastSent = window.systemStats.net_sent;
        let lastRecv = window.systemStats.net_recv;

        const netUpText = document.getElementById("netUpText");
        const netDownText = document.getElementById("netDownText");

        async function updateSystemStats() {
            try {
                const res = await fetch("/admin/system_stats");
                const data = await res.json();

                cpuChart.data.datasets[0].data[0] = data.cpu;
                cpuChart.data.datasets[0].data[1] = 100 - data.cpu;
                cpuChart.update();

                ramChart.data.datasets[0].data[0] = data.ram_percent;
                ramChart.data.datasets[0].data[1] = 100 - data.ram_percent;
                ramChart.update();

                diskChart.data.datasets[0].data[0] = data.disk_percent;
                diskChart.data.datasets[0].data[1] = 100 - data.disk_percent;
                diskChart.update();

                const upload = ((data.net_sent - lastSent) / 1024 / 1024).toFixed(2);
                const download = ((data.net_recv - lastRecv) / 1024 / 1024).toFixed(2);
                lastSent = data.net_sent;
                lastRecv = data.net_recv;

                netUpChart.data.datasets[0].data[0] = Math.min(upload * 5, 100);
                netUpChart.data.datasets[0].data[1] = 100 - netUpChart.data.datasets[0].data[0];
                netUpChart.update();

                netDownChart.data.datasets[0].data[0] = Math.min(download * 5, 100);
                netDownChart.data.datasets[0].data[1] = 100 - netDownChart.data.datasets[0].data[0];
                netDownChart.update();

                if (netUpText) netUpText.textContent = `${upload} MB/s`;
                if (netDownText) netDownText.textContent = `${download} MB/s`;

                if (document.getElementById("cpuText")) document.getElementById("cpuText").textContent = `${data.cpu}%`;
                if (document.getElementById("ramText")) document.getElementById("ramText").textContent = `${data.ram_used} / ${data.ram_total} GB (${data.ram_percent}%)`;
                if (document.getElementById("diskText")) document.getElementById("diskText").textContent = `${data.disk_used} / ${data.disk_total} GB (${data.disk_percent}%)`;

            } catch (err) { console.error("Error al actualizar stats:", err); }
        }

        setInterval(updateSystemStats, 1000);
    }

    // ===============================
    // IMPORT PLAYLIST YT
    // ===============================

    async function importYT() {
        const url = document.getElementById("yt-url").value;

        const res = await fetch("/import_youtube_playlist", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url})
        });

        const data = await res.json();

        alert(JSON.stringify(data));
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
    window.importYT = importYT;

    window.playSongByName = name => {
        const index = getSongs().findIndex(s => s.toLowerCase() === name.toLowerCase());
        if (index !== -1) loadSong(index);
    };

    // ===============================
    // INITIAL LOAD
    // ===============================
    if (player && getSongs().length > 0) loadSong(currentSongIndex);

});