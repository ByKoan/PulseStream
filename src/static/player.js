// player.js
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

        // Media Session API
        if ('mediaSession' in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: songs[currentSongIndex],
                artist: "Desconocido",
                album: "MusicCloud",
                artwork: [
                    { src: "https://via.placeholder.com/96", sizes: "96x96", type: "image/png" }
                ]
            });
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

        // Inicializamos gráficos
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

                // ======================
                // Actualizar gráficas
                // ======================
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

                // ======================
                // Actualizar valores en HTML
                // ======================
                document.getElementById("cpuText").textContent = `${data.cpu}%`;
                document.getElementById("ramText").textContent = `${data.ram_used} / ${data.ram_total} GB (${data.ram_percent}%)`;
                document.getElementById("diskText").textContent = `${data.disk_used} / ${data.disk_total} GB (${data.disk_percent}%)`;
                netUpText.textContent = `${upload} MB/s`;
                netDownText.textContent = `${download} MB/s`;

            } catch (err) {
                console.error("Error al actualizar stats:", err);
            }
        }

        setInterval(updateSystemStats, 1000);
    }

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

    if ("mediaSession" in navigator) {
        navigator.mediaSession.setActionHandler("play", () => player.play());
        navigator.mediaSession.setActionHandler("pause", () => player.pause());
        navigator.mediaSession.setActionHandler("previoustrack", () => handlePreviousClick());
        navigator.mediaSession.setActionHandler("nexttrack", () => handleNextClick());
    }

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