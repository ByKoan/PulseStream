// =============================================================================
// admin.js — Panel de administración
// Usado en: admin_panel.html
//
// Responsabilidades:
//   - Menú desplegable de navegación
//   - Banear y desbanear usuarios (con input de horas inline)
//   - Cambiar contraseña de un usuario (input inline)
//   - Cambiar el rol de un usuario (select inline)
//   - Confirmar eliminación de usuario antes de enviar el formulario
//   - Gráficas de uso del servidor en tiempo real (CPU, RAM, disco, red)
//     con polling cada 1 segundo a /admin/system_stats
//   - Estadísticas de la BD en tiempo real (usuarios, canciones, plays, top)
//     con polling cada 5 segundos a /admin/server_stats_db
//   - Importar playlist de YouTube desde el panel (función auxiliar)
//
// Endpoints que consume:
//   GET  /admin/system_stats     → CPU, RAM, disco, red del servidor (cada 1s)
//   GET  /admin/server_stats_db  → estadísticas de la BD (cada 5s)
//   POST /import_youtube_playlist → importar playlist de YouTube
//   (el resto de acciones van por submit de formulario HTML estándar)
//
// Dependencias externas:
//   Chart.js (cargado en el HTML) — para las gráficas tipo doughnut
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {

    // ===============================
    // MENÚ DESPLEGABLE DE NAVEGACIÓN
    // ===============================
    window.toggleMenu = function () {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    document.addEventListener("click", function (e) {
        const menu = document.getElementById("dropdownMenu");
        const btn = document.querySelector(".menu-toggle");
        if (!menu || !btn) return;
        if (!menu.contains(e.target) && !btn.contains(e.target)) {
            menu.classList.remove("show");
        }
    });

    // ===============================
    // BAN / UNBAN DE USUARIOS
    // Los botones .ban revelan un input para introducir las horas de baneo.
    // En el primer clic muestran el input; en el segundo validan y envían el form.
    // Los botones .unban envían directamente el formulario sin confirmación.
    // ===============================
    document.querySelectorAll(".ban").forEach(btn => {
        btn.addEventListener("click", () => {
            const form = btn.closest("form");
            const input = form?.querySelector(".ban-hours-input");
            if (!input) return;

            if (input.style.display === "none") {
                // Primer clic: muestra el input de horas
                input.style.display = "inline-block";
                input.focus();
            } else {
                // Segundo clic: valida el valor y envía el formulario
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
            btn.closest("form").submit();
        });
    });

    // ===============================
    // CAMBIAR CONTRASEÑA (inline)
    // El botón .change-password-btn revela un input de contraseña en la misma fila.
    // En el primer clic muestra el input; en el segundo valida y envía el form.
    // Usa event delegation para gestionar todos los botones de la tabla de usuarios.
    // ===============================
    document.addEventListener("click", e => {
        if (!e.target.classList.contains("change-password-btn")) return;
        const form = e.target.closest("form");
        const input = form?.querySelector(".password-input");
        if (!input) return;

        if (!input.style.display || input.style.display === "none") {
            // Primer clic: muestra el input de contraseña
            input.style.display = "inline-block";
            input.focus();
        } else {
            // Segundo clic: valida y envía el formulario
            if (!input.value.trim()) {
                alert("Introduce una contraseña válida");
                input.focus();
                return;
            }
            form.submit();
        }
    });

    // ===============================
    // CAMBIAR ROL DE USUARIO (inline)
    // El botón .role-btn revela un <select> con los roles disponibles.
    // En el primer clic muestra el select; en el segundo valida y envía el form.
    // stopPropagation en el select evita que el clic sobre él cierre el menú nav.
    // ===============================
    document.querySelectorAll(".role-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const form = btn.closest(".role-form");
            const select = form?.querySelector(".role-select");
            if (!select) return;

            if (!select.style.display || select.style.display === "none") {
                // Primer clic: muestra el select de roles
                select.style.display = "inline-block";
                select.focus();
            } else {
                // Segundo clic: valida la selección y envía el formulario
                if (!select.value) {
                    alert("Selecciona un rol válido");
                    select.focus();
                    return;
                }
                form.submit();
            }
        });
    });

    // Evita que el clic sobre el select cierre accidentalmente el menú de nav
    document.querySelectorAll(".role-select").forEach(select => {
        select.addEventListener("click", e => e.stopPropagation());
    });

    // ===============================
    // ELIMINAR USUARIO (confirmación)
    // Los botones .delete abren un confirm() antes de enviar el formulario.
    // Si el usuario cancela, se llama preventDefault() para no enviar.
    // ===============================
    document.querySelectorAll(".delete").forEach(btn => {
        btn.addEventListener("click", e => {
            if (!confirm("¿Estás seguro de eliminar este usuario?")) {
                e.preventDefault(); // Cancela el submit del formulario
            }
        });
    });

    // ===============================
    // GRÁFICAS DE RECURSOS DEL SERVIDOR (tiempo real)
    // Solo se inicializa si window.systemStats existe (inyectado por el template HTML
    // con los valores iniciales del servidor al cargar la página).
    //
    // Crea 5 gráficas doughnut con Chart.js:
    //   cpuChart     → porcentaje de CPU
    //   ramChart     → porcentaje de RAM
    //   diskChart    → porcentaje de disco
    //   netUpChart   → MB/s de subida (calculado como delta entre actualizaciones)
    //   netDownChart → MB/s de bajada (calculado como delta entre actualizaciones)
    //
    // Polling a /admin/system_stats cada 1 segundo para actualizar las gráficas.
    // ===============================
    if (window.systemStats) {

        // Helper: crea una gráfica doughnut en el canvas con el id dado
        const createChart = (id, value, color) => new Chart(document.getElementById(id), {
            type: "doughnut",
            data: {
                datasets: [{
                    data: [value, 100 - value], // [usado, libre]
                    backgroundColor: [color, "#333"]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });

        // Inicializa las gráficas con los valores del primer render (desde el servidor)
        const cpuChart = createChart("cpuChart", window.systemStats.cpu, "#ff6384");
        const ramChart = createChart("ramChart", window.systemStats.ram, "#36a2eb");
        const diskChart = createChart("diskChart", window.systemStats.disk, "#ffce56");
        const netUpChart = createChart("netUpChart", 0, "#4bc0c0");    // Red: empieza en 0
        const netDownChart = createChart("netDownChart", 0, "#ff9f40"); // Red: empieza en 0

        // Guarda los bytes de red del render inicial para calcular el delta en cada actualización
        let lastSent = window.systemStats.net_sent;
        let lastRecv = window.systemStats.net_recv;

        const netUpText = document.getElementById("netUpText");
        const netDownText = document.getElementById("netDownText");

        // Actualiza todas las gráficas con los datos más recientes del servidor
        async function updateSystemStats() {
            try {
                // GET /admin/system_stats — devuelve CPU, RAM, disco y bytes de red acumulados
                const res = await fetch("/admin/system_stats");
                const data = await res.json();

                // Actualiza CPU
                cpuChart.data.datasets[0].data = [data.cpu, 100 - data.cpu];
                cpuChart.update();

                // Actualiza RAM
                ramChart.data.datasets[0].data = [data.ram_percent, 100 - data.ram_percent];
                ramChart.update();

                // Actualiza disco
                diskChart.data.datasets[0].data = [data.disk_percent, 100 - data.disk_percent];
                diskChart.update();

                // Calcula MB/s de red como diferencia respecto a la medición anterior
                const upload = ((data.net_sent - lastSent) / 1024 / 1024).toFixed(2);
                const download = ((data.net_recv - lastRecv) / 1024 / 1024).toFixed(2);
                lastSent = data.net_sent;
                lastRecv = data.net_recv;

                // Escala la velocidad para la gráfica (x5 para hacerla más visible; máx 100%)
                const upVal = Math.min(upload * 5, 100);
                const downVal = Math.min(download * 5, 100);
                netUpChart.data.datasets[0].data = [upVal, 100 - upVal];
                netUpChart.update();
                netDownChart.data.datasets[0].data = [downVal, 100 - downVal];
                netDownChart.update();

                // Actualiza los textos de los labels de las gráficas
                if (netUpText) netUpText.textContent = `${upload} MB/s`;
                if (netDownText) netDownText.textContent = `${download} MB/s`;
                if (document.getElementById("cpuText"))
                    document.getElementById("cpuText").textContent = `${data.cpu}%`;
                if (document.getElementById("ramText"))
                    document.getElementById("ramText").textContent =
                        `${data.ram_used} / ${data.ram_total} GB (${data.ram_percent}%)`;
                if (document.getElementById("diskText"))
                    document.getElementById("diskText").textContent =
                        `${data.disk_used} / ${data.disk_total} GB (${data.disk_percent}%)`;

            } catch (err) {
                console.error("Error al actualizar stats:", err);
            }
        }

        // Actualiza las gráficas de hardware cada segundo
        setInterval(updateSystemStats, 1000);

        // ===============================
        // ESTADÍSTICAS DE LA BASE DE DATOS (tiempo real)
        // Muestra en el panel el total de usuarios, canciones, reproducciones,
        // la canción más escuchada y el usuario con más canciones.
        // Polling a /admin/server_stats_db cada 5 segundos (menos frecuente que hardware).
        // ===============================
        async function updateServerStats() {
            try {
                // GET /admin/server_stats_db
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

                // Muestra título y plays de la canción más escuchada (o "Sin datos")
                if (statTopSong) {
                    statTopSong.innerHTML = data.top_song_title
                        ? `${data.top_song_title}<br>(${data.top_song_plays} plays)`
                        : "Sin datos";
                }

                // Muestra el usuario con más canciones y su total (o "Sin datos")
                if (statTopUser) {
                    statTopUser.innerHTML = data.top_user_name
                        ? `${data.top_user_name}<br>(${data.top_user_total} canciones)`
                        : "Sin datos";
                }
            } catch (err) {
                console.error("Error al actualizar server stats:", err);
            }
        }

        // Actualiza las estadísticas de BD cada 5 segundos
        setInterval(updateServerStats, 5000);
    }
});
