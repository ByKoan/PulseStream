// =============================================================================
// login.js — Página de login / registro
// Usado en: login.html
//
// Responsabilidades:
//   - Gestionar el registro de nuevos usuarios vía botón "Registrarse"
//   - Enviar credenciales al backend y mostrar resultado
//   - Recargar la página tras registro exitoso para que el usuario inicie sesión
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {

    // Botón de registro (solo existe en la página de login, no en la de registro puro)
    const registerBtn = document.getElementById("registerBtn");
    if (!registerBtn) return; // Si no existe el botón, no hay nada que hacer

    registerBtn.addEventListener("click", async () => {

        // Recoge los valores del formulario
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        // Validación básica: ambos campos son obligatorios
        if (!username || !password) {
            alert("Todos los campos son obligatorios");
            return;
        }

        // La URL del endpoint viene en el atributo data-url del botón
        // (así el HTML controla a qué ruta apunta sin hardcodear en JS)
        const url = registerBtn.dataset.url;

        try {
            // POST /register — envía credenciales en JSON
            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();

            if (data.success) {
                alert(data.message);
                window.location.reload(); // Recarga para que el usuario pueda iniciar sesión
            } else {
                alert(data.error); // Muestra el error devuelto por el backend (ej: "usuario ya existe")
            }
        } catch (err) {
            console.error(err);
            alert("Ocurrió un error al registrar el usuario");
        }
    });
});
