import { apiFetch, escapeHtml, toast } from './utils.js';

export async function renderYamlEditor(container) {
  container.innerHTML = `<div class="spinner" style="margin:40px auto;display:block"></div>`;
  try {
    const data = await apiFetch('/api/config/yaml');
    container.innerHTML = `
      <div class="card">
        <div class="card-title">Editor Raw YAML</div>
        <div class="btn-group" style="margin-bottom:14px">
          <button class="btn btn-ghost btn-sm" id="yaml-reload">&#8635; Recarregar</button>
          <button class="btn btn-ghost btn-sm" id="yaml-validate">&#10003; Validar</button>
          <button class="btn btn-primary" id="yaml-save">Salvar</button>
        </div>
        <textarea class="yaml-textarea" id="yaml-content">${escapeHtml(data.yaml_content)}</textarea>
        <div id="yaml-error"></div>
      </div>`;
    document.getElementById('yaml-reload').addEventListener('click',   () => renderYamlEditor(container));
    document.getElementById('yaml-validate').addEventListener('click', validateYaml);
    document.getElementById('yaml-save').addEventListener('click',     saveYaml);
  } catch(e) {
    container.innerHTML = `<div class="notify-bar error">${escapeHtml(e.message)}</div>`;
  }
}

async function validateYaml() {
  const content = document.getElementById('yaml-content').value;
  const errEl   = document.getElementById('yaml-error');
  try {
    await apiFetch('/api/config/yaml', { method:'PUT', body: JSON.stringify({ yaml_content: content }) });
    errEl.innerHTML = `<div class="notify-bar success">&#10003; YAML válido!</div>`;
  } catch(e) {
    errEl.innerHTML = `<div class="yaml-error">${escapeHtml(e.message)}</div>`;
  }
}

async function saveYaml() {
  const content = document.getElementById('yaml-content').value;
  const errEl   = document.getElementById('yaml-error');
  window.__hueApp.showLoading();
  try {
    await apiFetch('/api/config/yaml', { method:'PUT', body: JSON.stringify({ yaml_content: content }) });
    errEl.innerHTML = `<div class="notify-bar success">&#10003; YAML salvo com sucesso!</div>`;
    toast('YAML salvo!', 'success');
  } catch(e) {
    errEl.innerHTML = `<div class="yaml-error">${escapeHtml(e.message)}</div>`;
  } finally { window.__hueApp.hideLoading(); }
}
