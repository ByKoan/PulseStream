document.addEventListener("DOMContentLoaded", () => {


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
    // BAN / UNBAN
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

    document.querySelectorAll(".unban").forEach(btn => {
        btn.addEventListener("click", () => {
            const form = btn.closest("form");
            form.submit();
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
    // DELETE USER
    // ===============================
    document.querySelectorAll(".delete").forEach(btn => {
        btn.addEventListener("click", e => {
            if (!confirm("¿Estás seguro de eliminar este usuario?")) {
                e.preventDefault();
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
        const ramChart = createChart("ramChart", window.systemStats.ram, "#36a2eb");
        const diskChart = createChart("diskChart", window.systemStats.disk, "#ffce56");
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

            } catch (err) {
                console.error("Error al actualizar stats:", err);
            }
        }

        setInterval(updateSystemStats, 1000);

        // ===============================
        // ESTADÍSTICAS DEL SERVIDOR (BD) EN TIEMPO REAL
        // ===============================
        async function updateServerStats() {
            try {
                const res = await fetch("/admin/server_stats_db");
                const data = await res.json();

                const statUsers = document.getElementById("stat-users");
                const statSongs = document.getElementById("stat-songs");
                const statPlays = document.getElementById("stat-plays");
                const statTopSong = document.getElementById("stat-top-song");
                const statTopUser = document.getElementById("stat-top-user");

                if (statUsers) statUsers.textContent = data.total_users;
                if (statSongs) statSongs.textContent = data.total_songs;
                if (statPlays) statPlays.textContent = data.total_plays;

                if (statTopSong) {
                    statTopSong.innerHTML = data.top_song_title
                        ? `${data.top_song_title}<br>(${data.top_song_plays} plays)`
                        : "Sin datos";
                }

                if (statTopUser) {
                    statTopUser.innerHTML = data.top_user_name
                        ? `${data.top_user_name}<br>(${data.top_user_total} canciones)`
                        : "Sin datos";
                }
            } catch (err) {
                console.error("Error al actualizar server stats:", err);
            }
        }

        setInterval(updateServerStats, 5000);
    }

    // ===============================
    // IMPORT PLAYLIST YT (si existe input)
    // ===============================
    async function importYT() {
        const ytInput = document.getElementById("yt-url");
        if (!ytInput) return;

        const url = ytInput.value;

        try {
            const res = await fetch("/import_youtube_playlist", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({url})
            });

            const data = await res.json();
            alert(JSON.stringify(data));

        } catch (err) {
            alert("Error al importar playlist: " + err);
        }
    }

    window.importYT = importYT;
});