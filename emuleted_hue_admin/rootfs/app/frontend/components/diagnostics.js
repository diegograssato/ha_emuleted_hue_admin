import { apiFetch, escapeHtml } from './utils.js';

export function renderDiagnostics(container) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title">Diagnóstico do Emulated Hue</div>
      <p style="color:var(--text-muted);margin-bottom:16px;font-size:13px">Verifica se o serviço Emulated Hue está acessível na rede.</p>
      <button class="btn btn-primary" id="diag-run">&#128300; Executar Diagnóstico</button>
      <div id="diag-result" style="margin-top:16px"></div>
    </div>`;
  document.getElementById('diag-run').addEventListener('click', runDiag);
}

async function runDiag() {
  const res = document.getElementById('diag-result');
  res.innerHTML = `<div class="spinner" style="display:block;margin:20px auto"></div>`;
  try {
    const d = await apiFetch('/api/diagnostics');
    res.innerHTML = `
      <div class="card" style="margin-bottom:0">
        <div class="diag-row">
          <span class="diag-label">Porta acessível</span>
          <span class="diag-value"><span class="dot ${d.port_open?'dot-green':'dot-red'}"></span>${d.port_open?'Sim':'Não'}</span>
        </div>
        <div class="diag-row">
          <span class="diag-label">UPnP Respondendo</span>
          <span class="diag-value"><span class="dot ${d.upnp_reachable?'dot-green':'dot-red'}"></span>${d.upnp_reachable?'Sim':'Não'}</span>
        </div>
        <div class="diag-row">
          <span class="diag-label">Friendly Name</span>
          <span class="diag-value">${escapeHtml(d.friendly_name||'—')}</span>
        </div>
        <div class="diag-row">
          <span class="diag-label">Host</span>
          <span class="diag-value">${escapeHtml(d.host||'—')}</span>
        </div>
        <div class="diag-row">
          <span class="diag-label">Porta</span>
          <span class="diag-value">${escapeHtml(String(d.port||'—'))}</span>
        </div>
        ${d.error ? `<div class="diag-row"><span class="diag-label">Erro</span><span style="color:var(--danger)">${escapeHtml(d.error)}</span></div>` : ''}
      </div>`;
  } catch(e) {
    res.innerHTML = `<div class="notify-bar error">${escapeHtml(e.message)}</div>`;
  }
}
