// =============================================================================
// upload.js — Página de subida de canciones
// Usado en: upload.html
//
// Responsabilidades:
//   - Controlar el menú desplegable de navegación (dropdown)
//
// Nota: La subida real del archivo se gestiona directamente por el formulario
// HTML (multipart/form-data hacia POST /upload). Este script solo gestiona la UI.
// =============================================================================

document.addEventListener("DOMContentLoaded", function () {

    // ===============================
    // MENÚ DESPLEGABLE DE NAVEGACIÓN
    // Expone window.toggleMenu para que el botón del menú en el HTML
    // pueda llamarlo con onclick="toggleMenu()"
    // ===============================
    window.toggleMenu = function () {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    // Cierra el menú si el usuario hace clic en cualquier parte fuera de él
    document.addEventListener("click", function (event) {
        const menu = document.getElementById("dropdownMenu");
        const btn = document.querySelector(".menu-toggle");
        if (!menu || !btn) return;

        // Solo cierra si el clic NO fue dentro del menú ni en el botón que lo abre
        if (!menu.contains(event.target) && !btn.contains(event.target)) {
            menu.classList.remove("show");
        }
    });

    // Cierra el menú al pulsar Escape (accesibilidad)
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            const menu = document.getElementById("dropdownMenu");
            if (menu) menu.classList.remove("show");
        }
    });
});
