const EYE_OPEN_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
const EYE_OFF_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.45 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    btn.innerHTML = EYE_OFF_SVG;
    btn.setAttribute('aria-label', 'Hide password');
    btn.title = 'Hide password';
  } else {
    input.type = 'password';
    btn.innerHTML = EYE_OPEN_SVG;
    btn.setAttribute('aria-label', 'Show password');
    btn.title = 'Show password';
  }
}
window.togglePasswordVisibility = togglePasswordVisibility;

document.addEventListener('DOMContentLoaded', () => {
  const r = document.documentElement, s = localStorage.getItem('freshtrack-theme');
  if (s) r.dataset.theme = s;
  document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => {
    r.dataset.theme = r.dataset.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('freshtrack-theme', r.dataset.theme);
  });
  document.querySelector('[data-sidebar-toggle]')?.addEventListener('click', () => document.querySelector('#sidebar')?.classList.toggle('open'));
  document.querySelectorAll('[data-open-modal]').forEach(b => b.onclick = () => document.getElementById(b.dataset.openModal)?.showModal());
  document.querySelectorAll('[data-close-modal]').forEach(b => b.onclick = () => b.closest('dialog')?.close());
  document.querySelectorAll('[data-confirm]').forEach(f => f.onsubmit = e => {
    if (!confirm(f.dataset.confirm)) e.preventDefault();
  });
  document.querySelectorAll('.toast button').forEach(b => b.onclick = () => b.parentElement.remove());
  setTimeout(() => document.querySelectorAll('.toast').forEach(x => x.remove()), 4500);

  function chart(id, type) {
    const e = document.getElementById(id);
    if (!e) return;
    new Chart(e, {
      type,
      data: {
        labels: JSON.parse(e.dataset.labels),
        datasets: [{
          data: JSON.parse(e.dataset.values),
          backgroundColor: type === 'doughnut' ? ['#18794e', '#3269a8', '#d19a36', '#c45b50'] : 'rgba(24,121,78,.12)',
          borderColor: '#18794e',
          borderWidth: 2,
          tension: .35,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: type === 'doughnut', position: 'bottom' }
        }
      }
    });
  }

  chart('trendChart', 'line');
  chart('categoryChart', 'doughnut');

  document.querySelector('[data-global-search]')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') location.href = '/products?q=' + encodeURIComponent(e.target.value);
  });
});
