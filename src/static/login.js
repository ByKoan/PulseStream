document.addEventListener("DOMContentLoaded", () => {
    const registerBtn = document.getElementById("registerBtn");
    if (!registerBtn) return;

    registerBtn.addEventListener("click", async () => {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!username || !password) {
            alert("Todos los campos son obligatorios");
            return;
        }

        const url = registerBtn.dataset.url;

        try {
            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();

            if (data.success) {
                alert(data.message);
                window.location.reload(); // recarga para iniciar sesión
            } else {
                alert(data.error);
            }
        } catch (err) {
            console.error(err);
            alert("Ocurrió un error al registrar el usuario");
        }
    });
});