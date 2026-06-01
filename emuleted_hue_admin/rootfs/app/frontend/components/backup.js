import { apiFetch, escapeHtml, toast, API_BASE } from './utils.js';

export function renderBackup(container) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title">Criar Backup</div>
      <p style="color:var(--text-muted);margin-bottom:14px;font-size:13px">Cria um backup do configuration.yaml atual.</p>
      <div class="btn-group">
        <button class="btn btn-primary" id="bk-create">&#128190; Criar Backup Agora</button>
        <a class="btn btn-ghost" id="bk-dl-config" href="${API_BASE}/api/backup/download-config" download="configuration.yaml">&#8677; Download configuration.yaml</a>
      </div>
      <div id="bk-create-result" style="margin-top:12px"></div>
    </div>
    <div class="card">
      <div class="card-title">Restaurar Backup</div>
      <p style="color:var(--text-muted);margin-bottom:14px;font-size:13px">Selecione um arquivo .yaml de backup para restaurar.</p>
      <div class="flex-row">
        <input type="file" id="bk-file" accept=".yaml,.yml" style="color:var(--text)" />
        <button class="btn btn-danger" id="bk-restore">Restaurar</button>
      </div>
      <div id="bk-restore-result" style="margin-top:12px"></div>
    </div>
    <div class="card">
      <div class="card-title">Backups Disponíveis <button class="btn btn-ghost btn-sm" id="bk-refresh" style="margin-left:8px">&#8635;</button></div>
      <div id="bk-list"><div class="spinner" style="display:block;margin:20px auto"></div></div>
    </div>`;

  document.getElementById('bk-create').addEventListener('click', createBackup);
  document.getElementById('bk-restore').addEventListener('click', restoreBackup);
  document.getElementById('bk-refresh').addEventListener('click', loadList);
  loadList();
}

async function createBackup() {
  const res = document.getElementById('bk-create-result');
  window.__hueApp.showLoading();
  try {
    const data = await apiFetch('/api/backup', { method:'POST' });
    res.innerHTML = `<div class="notify-bar success">&#10003; Backup criado: <strong>${escapeHtml(data.filename)}</strong> (${(data.size_bytes/1024).toFixed(1)} KB)</div>`;
    toast('Backup criado!', 'success');
    loadList();
  } catch(e) { res.innerHTML = `<div class="notify-bar error">${escapeHtml(e.message)}</div>`; }
  finally { window.__hueApp.hideLoading(); }
}

async function restoreBackup() {
  const file = document.getElementById('bk-file').files[0];
  const res  = document.getElementById('bk-restore-result');
  if (!file) { res.innerHTML = '<div class="notify-bar warning">Selecione um arquivo primeiro.</div>'; return; }
  if (!await window.__hueApp.confirm(`Restaurar "${file.name}"? O configuration.yaml atual será sobrescrito.`)) return;
  const form = new FormData();
  form.append('file', file);
  window.__hueApp.showLoading();
  try {
    await fetch(`${window.location.pathname.replace(/\/$/,'')+''}/api/backup/restore`, { method:'POST', body: form });
    res.innerHTML = `<div class="notify-bar success">&#10003; Backup restaurado com sucesso!</div>`;
    toast('Backup restaurado!', 'success');
  } catch(e) { res.innerHTML = `<div class="notify-bar error">${escapeHtml(e.message)}</div>`; }
  finally { window.__hueApp.hideLoading(); }
}

async function loadList() {
  const el = document.getElementById('bk-list');
  try {
    const list = await apiFetch('/api/backup/list');
    if (!list.length) { el.innerHTML = `<p style="color:var(--text-muted);font-size:13px">Nenhum backup encontrado.</p>`; return; }
    el.innerHTML = `
      <div class="table-wrap">
        <table>
          <thead><tr><th>Arquivo</th><th>Tamanho</th><th>Data</th><th></th></tr></thead>
          <tbody>
            ${list.map(b => `<tr>
              <td class="text-bright">${escapeHtml(b.filename)}</td>
              <td>${(b.size_bytes/1024).toFixed(1)} KB</td>
              <td class="text-muted">${escapeHtml(b.created_at)}</td>
              <td><a class="btn btn-ghost btn-sm" href="${API_BASE}/api/backup/download/${encodeURIComponent(b.filename)}" download="${escapeHtml(b.filename)}">&#8677; Download</a></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  } catch(e) { el.innerHTML = `<div class="notify-bar error">${escapeHtml(e.message)}</div>`; }
}
