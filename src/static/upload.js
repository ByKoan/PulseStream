// =========================
// MENU DESPLEGABLE HORIZONTAL
// =========================

document.addEventListener('DOMContentLoaded', function() {

    // Función global para onclick inline
    window.toggleMenu = function() {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.toggle("show");
    };

    // Cerrar el menú si se hace clic fuera
    document.addEventListener('click', function(event) {
        const menu = document.getElementById("dropdownMenu");
        const btn = document.querySelector(".menu-toggle");
        if (!menu || !btn) return;
        if (!menu.contains(event.target) && !btn.contains(event.target)) {
            menu.classList.remove('show');
        }
    });

    // Cerrar el menú con la tecla Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === "Escape") {
            const menu = document.getElementById("dropdownMenu");
            if (menu) menu.classList.remove('show');
        }
    });

});