import { apiFetch, escapeHtml } from './utils.js';

export function renderAudit(container) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title">
        Log de Auditoria
        <span style="float:right;display:flex;align-items:center;gap:8px">
          <label style="font-size:12px;color:var(--text-muted)">Limite</label>
          <select id="audit-limit" style="width:90px">
            <option>50</option><option>100</option><option>250</option>
          </select>
          <button class="btn btn-ghost btn-sm" id="audit-refresh">&#8635;</button>
        </span>
      </div>
      <div id="audit-table"></div>
    </div>`;
  document.getElementById('audit-limit').addEventListener('change', loadAudit);
  document.getElementById('audit-refresh').addEventListener('click', loadAudit);
  loadAudit();
}

async function loadAudit() {
  const limit = document.getElementById('audit-limit').value;
  const el    = document.getElementById('audit-table');
  el.innerHTML = `<div class="spinner" style="display:block;margin:20px auto"></div>`;
  try {
    const logs = await apiFetch(`/api/audit?limit=${limit}`);
    if (!logs.length) { el.innerHTML = `<p style="color:var(--text-muted);font-size:13px">Nenhum registro de auditoria.</p>`; return; }
    el.innerHTML = `
      <div class="table-wrap">
        <table>
          <thead><tr><th>Data/Hora</th><th>Ação</th><th>Entity ID</th><th>Usuário</th><th>Detalhe</th></tr></thead>
          <tbody>
            ${logs.map(l=>`<tr>
              <td class="text-muted" style="white-space:nowrap">${escapeHtml(l.timestamp||'')}</td>
              <td><span class="badge badge-orange">${escapeHtml(l.action||'')}</span></td>
              <td class="text-bright">${escapeHtml(l.entity_id||'—')}</td>
              <td>${escapeHtml(l.user||'—')}</td>
              <td class="text-muted" style="font-size:12px">${escapeHtml(l.detail||'')}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  } catch(e) {
    el.innerHTML = `<div class="notify-bar error">${escapeHtml(e.message)}</div>`;
  }
}
