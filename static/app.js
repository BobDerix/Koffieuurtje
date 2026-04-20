'use strict';

// ---------------------------------------------------------------------------
// Last-update badge
// ---------------------------------------------------------------------------
async function loadStatus() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) return;
    const data = await res.json();
    const el = document.getElementById('update-time');
    if (el && data.last_update) {
      el.textContent = formatRelativeTime(data.last_update);
      document.getElementById('update-badge')?.classList.remove('d-none');
    }
  } catch (_) {}
}

function formatRelativeTime(isoString) {
  const date = new Date(isoString);
  const now  = new Date();
  const diff = Math.floor((now - date) / 60000); // minutes

  if (diff < 1)  return 'zojuist bijgewerkt';
  if (diff < 60) return `${diff} min geleden`;
  const hours = Math.floor(diff / 60);
  if (hours < 24) return `${hours} uur geleden`;
  const days = Math.floor(hours / 24);
  return `${days} dag${days !== 1 ? 'en' : ''} geleden`;
}

// ---------------------------------------------------------------------------
// Manual refresh
// ---------------------------------------------------------------------------
async function triggerRefresh() {
  const btn  = document.getElementById('refresh-btn');
  const icon = document.getElementById('refresh-icon');
  if (!btn) return;

  btn.disabled = true;
  icon?.classList.add('spin');

  try {
    const res  = await fetch('/api/refresh', { method: 'POST' });
    const data = await res.json();

    if (data.status === 'ok') {
      if (data.new_articles > 0) {
        showToast(`${data.new_articles} nieuw artikel${data.new_articles !== 1 ? 'en' : ''} opgehaald!`, 'success');
        // Reload page to show new articles after a short delay
        setTimeout(() => window.location.reload(), 1200);
      } else {
        showToast('Geen nieuwe artikelen gevonden.', 'info');
      }
    } else {
      showToast('Vernieuwen mislukt: ' + (data.message || 'onbekende fout'), 'danger');
    }
  } catch (err) {
    showToast('Verbindingsfout bij vernieuwen.', 'danger');
  } finally {
    btn.disabled = false;
    icon?.classList.remove('spin');
    loadStatus();
  }
}

// ---------------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------------
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
  }

  const icons = { success: 'check-circle-fill', danger: 'x-circle-fill', info: 'info-circle-fill' };
  const id = 'toast-' + Date.now();
  const html = `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi bi-${icons[type] || 'info-circle-fill'}"></i>
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast" aria-label="Sluiten"></button>
      </div>
    </div>`;
  container.insertAdjacentHTML('beforeend', html);
  const toastEl = document.getElementById(id);
  const toast   = new bootstrap.Toast(toastEl, { delay: 4000 });
  toast.show();
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// ---------------------------------------------------------------------------
// Auto-refresh every 5 minutes (update badge only, not page)
// ---------------------------------------------------------------------------
function startAutoStatusRefresh() {
  setInterval(loadStatus, 5 * 60 * 1000);
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  loadStatus();
  startAutoStatusRefresh();
});
