/**
 * Shared utilities: API client, toast, loading overlay.
 */

// ------------------------------------------------------------------ //
// API base path (respects HA ingress sub-path)
// ------------------------------------------------------------------ //
export const API_BASE = window.location.pathname.replace(/\/$/, '');

export async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try {
      const body = await resp.json();
      detail = body.detail || body.message || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  const ct = resp.headers.get('content-type') || '';
  if (ct.includes('application/json')) return resp.json();
  return resp.text();
}

// ------------------------------------------------------------------ //
// Toast notifications
// ------------------------------------------------------------------ //
const ICONS = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };

export function toast(message, type = 'success', duration = 4000) {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${ICONS[type] || ICONS.info}</span>
    <span class="toast-body">${escapeHtml(message)}</span>
    <span class="toast-close" role="button" tabindex="0">✕</span>
  `;
  const close = () => { el.remove(); };
  el.querySelector('.toast-close').addEventListener('click', close);
  el.querySelector('.toast-close').addEventListener('keydown', e => e.key === 'Enter' && close());
  container.appendChild(el);
  setTimeout(close, duration);
}

// ------------------------------------------------------------------ //
// Loading overlay
// ------------------------------------------------------------------ //
export function showLoading() {
  document.getElementById('loading-overlay').classList.remove('hidden');
}
export function hideLoading() {
  document.getElementById('loading-overlay').classList.add('hidden');
}

// ------------------------------------------------------------------ //
// HTML escape
// ------------------------------------------------------------------ //
export function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ------------------------------------------------------------------ //
// Tags input helper
// ------------------------------------------------------------------ //
export function initTagsInput(container, initialValues = []) {
  const values = [...initialValues];

  function render() {
    container.innerHTML = values
      .map(v => `<span class="tag">${escapeHtml(v)}<span class="tag-remove" data-val="${escapeHtml(v)}">✕</span></span>`)
      .join('') + `<input class="tags-input" type="text" placeholder="Adicionar..." />`;

    container.querySelectorAll('.tag-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = values.indexOf(btn.dataset.val);
        if (idx >= 0) { values.splice(idx, 1); render(); }
      });
    });

    const inp = container.querySelector('.tags-input');
    inp.addEventListener('keydown', e => {
      if ((e.key === 'Enter' || e.key === ',') && inp.value.trim()) {
        e.preventDefault();
        const val = inp.value.trim().replace(/,+$/, '');
        if (val && !values.includes(val)) { values.push(val); render(); }
      }
    });
  }

  render();
  return { getValues: () => [...values] };
}
