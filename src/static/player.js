document.addEventListener("DOMContentLoaded", () => {

    const player = document.getElementById("player");
    const audioSource = document.getElementById("audioSource");
    const currentSongTitle = document.getElementById("currentSongTitle");

    let currentSongIndex = 0;
    let shuffle = false;
    let loop = false;

    function loadSong(index) {
        if (songs.length === 0) return;

        if (index < 0) currentSongIndex = songs.length - 1;
        else if (index >= songs.length) currentSongIndex = 0;
        else currentSongIndex = index;

        audioSource.src = "/play/" + encodeURIComponent(songs[currentSongIndex]);
        player.load();
        player.play();

        currentSongTitle.textContent = songs[currentSongIndex];
        document.title = songs[currentSongIndex];

        // =========================
        // Media Session API (iOS + Android)
        // =========================
        if ('mediaSession' in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: songs[currentSongIndex],
                artist: "Desconocido",
                album: "MusicCloud",
                artwork: [
                    { src: "https://via.placeholder.com/96", sizes: "96x96", type: "image/png" }
                ]
            });

            navigator.mediaSession.setActionHandler('play', () => player.play());
            navigator.mediaSession.setActionHandler('pause', () => player.pause());
            navigator.mediaSession.setActionHandler('previoustrack', () => handlePreviousClick());
            navigator.mediaSession.setActionHandler('nexttrack', () => handleNextClick());
            navigator.mediaSession.setActionHandler('seekbackward', null);
            navigator.mediaSession.setActionHandler('seekforward', null);
            navigator.mediaSession.setActionHandler('seekto', null);
            navigator.mediaSession.setActionHandler('stop', null);
        }
    }

    function playPause() {
        if (player.paused) player.play();
        else player.pause();
    }

    function handleNextClick() {
        if (songs.length === 0) return;

        if (shuffle) {
            let newIndex;
            do { newIndex = Math.floor(Math.random() * songs.length); }
            while (newIndex === currentSongIndex && songs.length > 1);
            currentSongIndex = newIndex;
        } else {
            currentSongIndex++;
            if (currentSongIndex >= songs.length) currentSongIndex = 0;
        }

        loadSong(currentSongIndex);
    }

    function handlePreviousClick() {
        if (songs.length === 0) return;

        if (player.currentTime > 3) {
            player.currentTime = 0;
            player.play();
        } else {
            if (shuffle) {
                let newIndex;
                do { newIndex = Math.floor(Math.random() * songs.length); }
                while (newIndex === currentSongIndex && songs.length > 1);
                currentSongIndex = newIndex;
            } else {
                currentSongIndex--;
                if (currentSongIndex < 0) currentSongIndex = songs.length - 1;
            }
            loadSong(currentSongIndex);
        }
    }

    function toggleShuffle() {
        shuffle = !shuffle;
        document.getElementById("shuffleStatus").textContent =
            shuffle ? "Activado" : "Desactivado";
    }

    function toggleLoop() {
        loop = !loop;
        player.loop = loop;
        document.getElementById("loopStatus").textContent =
            loop ? "Activado" : "Desactivado";
    }

    // ===============================
    // ADMIN SYSTEM STATS CHARTS (real-time)
    // ===============================
    if (window.systemStats) {

        function createChart(id, value, color) {
            return new Chart(document.getElementById(id), {
                type: "doughnut",
                data: {
                    datasets: [{
                        data: [value, 100 - value],
                        backgroundColor: [color, "#333"]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
        }

        const cpuChart = createChart("cpuChart", window.systemStats.cpu, "#ff6384");
        const ramChart = createChart("ramChart", window.systemStats.ram_percent, "#36a2eb");
        const diskChart = createChart("diskChart", window.systemStats.disk_percent, "#ffce56");
        const netUpChart = createChart("netUpChart", 0, "#4bc0c0");
        const netDownChart = createChart("netDownChart", 0, "#ff9f40");

        const netUpText = document.getElementById("netUpText");
        const netDownText = document.getElementById("netDownText");

        let lastSent = window.systemStats.net_sent;
        let lastRecv = window.systemStats.net_recv;

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

                netUpChart.data.datasets[0].data[0] = Math.min(upload*5, 100);
                netUpChart.data.datasets[0].data[1] = 100 - netUpChart.data.datasets[0].data[0];
                netUpChart.update();

                netDownChart.data.datasets[0].data[0] = Math.min(download*5, 100);
                netDownChart.data.datasets[0].data[1] = 100 - netDownChart.data.datasets[0].data[0];
                netDownChart.update();

                netUpText.textContent = `${upload} MB/s`;
                netDownText.textContent = `${download} MB/s`;

                document.getElementById("cpuText").textContent = `${data.cpu}%`;
                document.getElementById("ramText").textContent = `${data.ram_used} / ${data.ram_total} GB (${data.ram_percent}%)`;
                document.getElementById("diskText").textContent = `${data.disk_used} / ${data.disk_total} GB (${data.disk_percent}%)`;

            } catch (err) {
                console.error("Error al actualizar stats:", err);
            }
        }

        setInterval(updateSystemStats, 1000);
    }

    async function updateServerStats(){
        const res = await fetch("/admin/server_stats")
        const data = await res.json()

        document.getElementById("totalUsers").textContent = data.total_users
        document.getElementById("activeUsers").textContent = data.active_users
        document.getElementById("totalSongs").textContent = data.total_songs
    }

    // ===============================
    // BORRAR CANCIONES (sin recargar)
    // ===============================
    document.querySelectorAll('.delete-song-btn').forEach(btn => {

        btn.addEventListener('click', async () => {

            const filename = btn.dataset.filename;
            if (!filename) return;

            const confirmDelete = confirm(`¿Estás seguro de que quieres borrar "${filename}"?`);
            if (!confirmDelete) return;

            try {

                const res = await fetch('/delete_song', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ filename })
                });

                const data = await res.json();

                if (data.success) {

                    const songItem = btn.closest(".song-item");
                    if (songItem) songItem.remove();

                    songs = songs.filter(song => song !== filename);

                    alert(`"${filename}" borrada correctamente`);

                } else {
                    alert(`Error: ${data.error}`);
                }

            } catch (err) {
                alert(`Error al borrar la canción: ${err}`);
            }

        });

    });

    async function loadPlaylist(playlistId) {
        try {
            const res = await fetch(`/playlist/${playlistId}`);
            const data = await res.json();

            if (res.status === 404) {
                alert(data.error);
                window.location.href = "/create_playlist";
                return;
            }

            songs = data.songs;
            currentSongIndex = 0;
            loadSong(currentSongIndex);

        } catch (err) {
            console.error("Error al cargar la playlist:", err);
            alert("Error al cargar la playlist.");
        }
    }

    // ===============================
    // REPRODUCIR CANCIÓN POR NOMBRE (para búsquedas)
    // ===============================
    function playSongByName(name) {
        const index = songs.findIndex(s => s.toLowerCase() === name.toLowerCase());
        if (index !== -1) {
            loadSong(index);
        } else {
            console.warn("Canción no encontrada:", name);
        }
    }

    async function addToPlaylist(filename, playlistId) {
        try {
            const res = await fetch("/add_to_playlist", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename, playlist_id: playlistId })
            });

            const text = await res.text();
            console.log("Respuesta servidor:", text);

            const data = JSON.parse(text);

            if (data.success) {
                alert(`"${filename}" añadida a la playlist`);
            } else {
                alert(`Error: ${data.error}`);
            }

        } catch (err) {
            alert("Error al añadir la canción: " + err);
        }
    }

    // ===============================
    // Funcionalidades html playlist
    // ===============================

    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const songList = document.getElementById("songList");
    const resetSearch = document.getElementById("resetSearch");

    searchForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = searchInput.value.toLowerCase();
        const items = songList.querySelectorAll(".song-item");

        items.forEach(item => {
            const title = item.querySelector(".song-title").textContent.toLowerCase();
            item.style.display = title.includes(query) ? "" : "none";
        });

        // Reproducir la primera canción visible si hay coincidencias
        const firstVisible = songList.querySelector(".song-item:not([style*='display: none']) .song-title");
        if (firstVisible) {
            playSongByName(firstVisible.textContent);
        }
    });

    // ===============================
    // AÑADIR CANCIONES A PLAYLIST
    // ===============================
    document.querySelectorAll(".add-to-playlist").forEach(container => {

        const addBtn = container.querySelector(".add-btn");
        const select = container.querySelector(".playlist-select");

        addBtn.addEventListener("click", (e) => {

            e.stopPropagation();

            const isOpen = select.style.display === "inline-block";

            document.querySelectorAll(".playlist-select").forEach(s => {
                s.style.display = "none";
            });

            if (!isOpen) {
                select.style.display = "inline-block";
            }
        });

        select.addEventListener("click", (e) => {
            e.stopPropagation();
        });

        select.addEventListener("change", async () => {

            const playlistId = select.value;
            if (!playlistId) return;

            const songItem = container.closest(".song-item");
            const filename = songItem.dataset.filename;

            await addToPlaylist(filename, playlistId);

            select.style.display = "none";
            select.selectedIndex = 0;
        });

    });

    document.addEventListener("click", () => {
        document.querySelectorAll(".playlist-select").forEach(s => {
            s.style.display = "none";
        });
    });

    // ===============================
    // QUITAR CANCIONES DE PLAYLIST
    // ===============================

    document.querySelectorAll(".remove-from-playlist").forEach(btn => {

        btn.addEventListener("click", async () => {

            const filename = btn.dataset.filename
            const playlistId = btn.dataset.playlist

            if(!confirm(`Quitar "${filename}" de la playlist?`)) return

            try {

                const res = await fetch("/remove_from_playlist", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        filename: filename,
                        playlist_id: playlistId
                    })
                })

                const data = await res.json()

                if(data.success){

                    const songItem = btn.closest(".song-item")
                    songItem.remove();
                    location.reload();

                } else {

                    alert(data.error)

                }

            } catch(err){

                alert("Error: " + err)

            }

        })

    })

    document.addEventListener("click", () => {
        document.querySelectorAll(".playlist-select").forEach(s => {
            s.style.display = "none";
        });
    });

    resetSearch.addEventListener("click", () => {
        searchInput.value = "";
        const items = songList.querySelectorAll(".song-item");
        items.forEach(item => item.style.display = "");
    });

    // Exponer la función al HTML
    window.playSongByName = playSongByName;

    setInterval(updateServerStats, 5000)

    // ===============================
    // Reproducción final y mediaSession
    // ===============================
    player.addEventListener("ended", () => {
        if (loop) {
            loadSong(currentSongIndex);
            return;
        }
        handleNextClick();
    });

    // Exponer funciones al HTML
    window.loadSong = loadSong;
    window.playPause = playPause;
    window.handleNextClick = handleNextClick;
    window.handlePreviousClick = handlePreviousClick;
    window.toggleShuffle = toggleShuffle;
    window.toggleLoop = toggleLoop;

    // Cargar primera canción automáticamente
    loadSong(0);
});