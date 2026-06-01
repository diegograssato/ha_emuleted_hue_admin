import { apiFetch, escapeHtml } from './utils.js';

export async function renderDashboard(container) {
  container.innerHTML = `
    <div id="dash-hue-check"></div>
    <div id="dash-content"><div class="spinner" style="margin:40px auto;display:block"></div></div>
  `;
  await checkEmulatedHue();
  await loadDashboard();
}

async function checkEmulatedHue() {
  const el = document.getElementById('dash-hue-check');
  if (!el) return;
  try {
    const data = await apiFetch('/api/dashboard/status');
    if (data.component_loaded) {
      el.innerHTML = `<div class="alert-banner success">&#10003; <strong>Emulated Hue</strong> está carregado e ativo no Home Assistant.</div>`;
    } else {
      el.innerHTML = `
        <div class="alert-banner warning">
          <div class="alert-banner-title">&#9888; Emulated Hue não está carregado no Home Assistant</div>
          <p>Adicione o bloco abaixo ao seu <strong>configuration.yaml</strong> e reinicie o HA:</p>
          <div class="code-block">${escapeHtml(data.suggestion || '')}</div>
          <div class="flex-row">
            <button class="btn btn-primary btn-sm" id="dash-goto-yaml">&#128196; Abrir Editor YAML</button>
            <a class="btn btn-ghost btn-sm" href="https://www.home-assistant.io/integrations/emulated_hue/" target="_blank" rel="noopener">&#128279; Documentação</a>
          </div>
        </div>`;
      document.getElementById('dash-goto-yaml')?.addEventListener('click', () => window.__hueApp.switchTab('yaml'));
    }
  } catch (_) { el.innerHTML = ''; }
}

async function loadDashboard() {
  const content = document.getElementById('dash-content');
  try {
    const data = await apiFetch('/api/dashboard');
    content.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-label">Total de Entidades</div><div class="stat-value">${data.total_entities}</div></div>
        <div class="stat-card"><div class="stat-label">Entidades Expostas</div><div class="stat-value green">${data.exposed_entities}</div></div>
        <div class="stat-card"><div class="stat-label">Ocultas</div><div class="stat-value red">${data.hidden_entities}</div></div>
        <div class="stat-card"><div class="stat-label">Status</div><div class="stat-value orange" style="font-size:14px;padding-top:6px"><span class="dot ${data.emulated_hue_status==='configured'?'dot-green':'dot-red'}"></span>${escapeHtml(data.emulated_hue_status)}</div></div>
      </div>
      <div class="card">
        <div class="card-title">Informações de Configuração</div>
        <table>
          <tbody>
            <tr><td class="text-muted" style="width:200px">Host IP</td><td class="text-bright">${escapeHtml(data.host_ip||'—')}</td></tr>
            <tr><td class="text-muted">Porta</td><td class="text-bright">${escapeHtml(String(data.listen_port||'—'))}</td></tr>
            <tr><td class="text-muted">Expose by Default</td><td class="text-bright">${data.expose_by_default?'Sim':'Não'}</td></tr>
            <tr><td class="text-muted">Última Modificação</td><td class="text-bright">${escapeHtml(data.last_modified||'—')}</td></tr>
          </tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-title">Ações Rápidas</div>
        <div class="btn-group">
          <button class="btn btn-primary" id="dash-go-entities">Gerenciar Entidades</button>
          <button class="btn btn-ghost"   id="dash-go-config">Configuração Geral</button>
          <button class="btn btn-success" id="dash-reload">&#9654; Reload Emulated Hue</button>
        </div>
      </div>

      <!-- Restart progress card (oculto inicialmente) -->
      <div id="restart-progress" class="card hidden" style="border:1px solid var(--primary)">
        <div class="card-title" style="color:var(--primary)">&#9654; Reiniciando Home Assistant…</div>
        <div id="restart-steps" style="margin-bottom:14px"></div>
        <div class="progress-bar-wrap" style="background:var(--surface2);border-radius:6px;height:8px;overflow:hidden;margin-bottom:10px">
          <div id="restart-bar" style="height:100%;background:var(--primary);width:0%;transition:width 0.5s ease"></div>
        </div>
        <p id="restart-status-text" style="color:var(--text-muted);font-size:13px;margin:0"></p>
      </div>`;

    document.getElementById('dash-go-entities').addEventListener('click', () => window.__hueApp.switchTab('entities'));
    document.getElementById('dash-go-config').addEventListener('click',   () => window.__hueApp.switchTab('config'));
    document.getElementById('dash-reload').addEventListener('click', () => startReload());
  } catch (e) {
    content.innerHTML = `<div class="notify-bar error">Erro ao carregar dashboard: ${escapeHtml(e.message)}</div>`;
  }
}

async function startReload() {
  if (!await window.__hueApp.confirm('O Home Assistant será reiniciado para aplicar as mudanças do Emulated Hue. Confirma?')) return;

  const progressCard = document.getElementById('restart-progress');
  const stepsEl      = document.getElementById('restart-steps');
  const barEl        = document.getElementById('restart-bar');
  const statusEl     = document.getElementById('restart-status-text');
  const reloadBtn    = document.getElementById('dash-reload');

  reloadBtn.disabled = true;
  progressCard.classList.remove('hidden');
  progressCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  const steps = [
    { label: 'Enviando comando de restart ao Home Assistant…', pct: 15 },
    { label: 'Aguardando HA encerrar serviços…',               pct: 35 },
    { label: 'HA reiniciando — aguarde…',                      pct: 60 },
    { label: 'Verificando se HA voltou online…',               pct: 80 },
    { label: 'Finalizando…',                                    pct: 95 },
  ];

  function setStep(idx, extra = '') {
    const step = steps[idx];
    stepsEl.innerHTML = steps.map((s, i) => `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;color:${i<idx?'var(--success)':i===idx?'var(--text-bright)':'var(--text-muted)'}">
        <span style="font-size:14px">${i < idx ? '&#10003;' : i === idx ? '&#9654;' : '&#9675;'}</span>
        <span style="font-size:13px">${s.label}</span>
      </div>`).join('');
    barEl.style.width = step.pct + '%';
    statusEl.textContent = extra;
  }

  // Passo 0: enviar o request
  setStep(0);
  try {
    await apiFetch('/api/reload', { method: 'POST' });
  } catch (e) {
    // TypeError = erro de rede (fetch falhou) — HA pode já estar reiniciando
    if (e instanceof TypeError) {
      setStep(1, 'Conexão perdida — HA provavelmente já está reiniciando…');
    } else {
      // Erro HTTP real (4xx/5xx) — falha confirmada. Exibe a mensagem completa.
      const isConfigError = e.message && e.message.toLowerCase().includes('not valid');
      const label = isConfigError
        ? '&#9888; Configuração inválida — o HA recusou o restart:'
        : '&#10007; Falha ao enviar comando:';
      stepsEl.innerHTML = `
        <div class="notify-bar error" style="white-space:pre-wrap;word-break:break-word">
          ${label}<br><br><strong>${escapeHtml(e.message)}</strong>
        </div>`;
      barEl.style.background = 'var(--danger)';
      barEl.style.width = '100%';
      reloadBtn.disabled = false;
      return;
    }
  }

  // Passos 1-3: espera + polling
  setStep(1);
  await delay(3000);
  setStep(2);
  await delay(4000);
  setStep(3);

  // Polling: tenta /api/reload/ping até 60 segundos
  const MAX_WAIT = 60;
  const INTERVAL = 3;
  let elapsed = 0;
  let online = false;

  while (elapsed < MAX_WAIT) {
    await delay(INTERVAL * 1000);
    elapsed += INTERVAL;
    statusEl.textContent = `Tentando reconectar… (${elapsed}s / ${MAX_WAIT}s)`;
    try {
      const res = await fetch(baseUrl() + '/api/reload/ping', { signal: AbortSignal.timeout(3000) });
      if (res.ok) { online = true; break; }
    } catch (_) { /* HA ainda offline */ }
  }

  if (online) {
    setStep(4, 'HA está online!');
    await delay(800);
    barEl.style.width = '100%';
    stepsEl.innerHTML += `<div style="color:var(--success);font-weight:600;margin-top:8px">&#10003; Home Assistant reiniciado com sucesso!</div>`;
    statusEl.textContent = '';
    window.__hueApp.toast('Home Assistant reiniciado com sucesso!', 'success');
    await delay(3000);
    progressCard.classList.add('hidden');
    reloadBtn.disabled = false;
    await loadDashboard();
  } else {
    setStep(4, 'Timeout — verifique o HA manualmente.');
    barEl.style.background = 'var(--danger)';
    barEl.style.width = '100%';
    window.__hueApp.toast('Timeout aguardando HA reiniciar.', 'error');
    reloadBtn.disabled = false;
  }
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function baseUrl() {
  return window.location.pathname.replace(/\/$/, '');
}
