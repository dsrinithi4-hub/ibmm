// One-time count-up animation for dashboard stat cards.
document.addEventListener("DOMContentLoaded", () => {
  const numbers = document.querySelectorAll(".stat-number[data-target]");

  numbers.forEach((el) => {
    const target = parseInt(el.dataset.target, 10) || 0;
    const duration = 700; // ms
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
});