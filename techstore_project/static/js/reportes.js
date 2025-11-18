// static/js/reportes.js

document.addEventListener("DOMContentLoaded", () => {
  const formVentasMes = document.getElementById("formReporteVentasMes");
  const formIvaTrimestre = document.getElementById("formReporteIvaTrimestre");

  if (formVentasMes) {
    formVentasMes.addEventListener("submit", () => {
      console.log("Generar reporte de ventas por mes...");
      // El action del form puede apuntar a un endpoint que genere el PDF.
    });
  }

  if (formIvaTrimestre) {
    formIvaTrimestre.addEventListener("submit", () => {
      console.log("Generar reporte IVA trimestre...");
    });
  }
});
