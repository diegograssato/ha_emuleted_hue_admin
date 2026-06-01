/**
 * Emulated Hue Manager — app.js
 * Vanilla ES Modules, horizontal tab navigation.
 */
import { renderDashboard }   from './components/dashboard.js';
import { renderConfig }      from './components/config-form.js';
import { renderEntities }    from './components/entities-table.js';
import { renderYamlEditor }  from './components/yaml-editor.js';
import { renderBackup }      from './components/backup.js';
import { renderDiagnostics } from './components/diagnostics.js';
import { renderAudit }       from './components/audit.js';
import { toast, showLoading, hideLoading } from './components/utils.js';

const RENDERERS = {
  dashboard:   renderDashboard,
  config:      renderConfig,
  entities:    renderEntities,
  yaml:        renderYamlEditor,
  backup:      renderBackup,
  diagnostics: renderDiagnostics,
  audit:       renderAudit,
};

const tabBtns   = document.querySelectorAll('.tab-btn[data-tab]');
const tabPanels = document.querySelectorAll('.tab-panel');

function switchTab(name) {
  tabBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  tabPanels.forEach(p => {
    const active = p.id === `tab-${name}`;
    p.classList.toggle('active', active);
    if (active && RENDERERS[name]) RENDERERS[name](p);
  });
}

tabBtns.forEach(b => b.addEventListener('click', () => switchTab(b.dataset.tab)));

// ── Confirm modal ────────────────────────────────────────────────
let _confirmResolve = null;
const confirmModal    = document.getElementById('confirm-modal');
const confirmMsg      = document.getElementById('confirm-modal-message');
const confirmOk       = document.getElementById('confirm-ok');
const confirmCancel   = document.getElementById('confirm-cancel');
const confirmBackdrop = document.getElementById('confirm-modal-backdrop');

function confirm(message) {
  return new Promise(resolve => {
    _confirmResolve = resolve;
    confirmMsg.textContent = message;
    confirmModal.classList.remove('hidden');
    confirmOk.focus();
  });
}

[confirmOk, confirmCancel, confirmBackdrop].forEach((el, i) => {
  el.addEventListener('click', () => {
    confirmModal.classList.add('hidden');
    if (_confirmResolve) _confirmResolve(i === 0);
    _confirmResolve = null;
  });
});

// ── Bootstrap ───────────────────────────────────────────────────
switchTab('dashboard');

window.__hueApp = { toast, showLoading, hideLoading, confirm, switchTab };
