// static/js/ventas.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("formVenta");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    // Aquí puedes añadir validaciones antes de que se envíe al servidor
    // Por ejemplo: que haya al menos un producto, que cantidades sean > 0, etc.
    console.log("Enviando venta...");
  });
});
