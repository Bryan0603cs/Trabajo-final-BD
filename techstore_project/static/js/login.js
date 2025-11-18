// static/js/login.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  const errorBox = document.getElementById("errorMessage");
  const serverError = document.getElementById("serverError");

  if (!form) {
    return;
  }

  // Si el servidor mandó un mensaje (login fallido), lo mostramos
  if (serverError && serverError.textContent.trim() !== "") {
    errorBox.textContent = serverError.textContent.trim();
    errorBox.classList.add("show");
  }

  form.addEventListener("submit", (event) => {
    const username = (form.username && form.username.value.trim()) || "";
    const password = (form.password && form.password.value.trim()) || "";

    if (!username || !password) {
      event.preventDefault();
      errorBox.textContent = "Por favor completa todos los campos";
      errorBox.classList.add("show");
    }
  });
});
