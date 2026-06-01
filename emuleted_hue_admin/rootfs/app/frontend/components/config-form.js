import { apiFetch, escapeHtml, toast, initTagsInput } from './utils.js';

export async function renderConfig(container) {
  container.innerHTML = `<div class="spinner" style="margin:40px auto;display:block"></div>`;
  try {
    const cfg = await apiFetch('/api/config');
    container.innerHTML = `
      <div class="card">
        <div class="card-title">Configuração Geral do Emulated Hue</div>
        <form id="cfg-form">
          <div class="form-row">
            <div class="form-group"><label>Host IP</label><input type="text" id="cfg-host-ip" value="${escapeHtml(cfg.host_ip||'')}" placeholder="192.168.1.X" /></div>
            <div class="form-group"><label>Listen Port</label><input type="number" id="cfg-port" value="${cfg.listen_port||80}" min="1" max="65535" /></div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Expose by Default</label>
              <label class="checkbox-row"><input type="checkbox" id="cfg-expose-default" ${cfg.expose_by_default?'checked':''}> Expor entidades por padrão</label>
            </div>
            <div class="form-group">
              <label>UPnP Bind Multicast</label>
              <label class="checkbox-row"><input type="checkbox" id="cfg-upnp" ${cfg.upnp_bind_multicast?'checked':''}> Ativar UPnP Multicast</label>
            </div>
          </div>
          <div class="form-group" style="margin-bottom:14px">
            <label>Off Maps To On Domains</label>
            <div class="tags-container" id="cfg-off-domains"></div>
          </div>
          <div class="form-group" style="margin-bottom:20px">
            <label>Exposed Domains</label>
            <div class="tags-container" id="cfg-exp-domains"></div>
          </div>
          <div class="btn-group">
            <button type="submit" class="btn btn-primary">Salvar Configuração</button>
            <button type="button" class="btn btn-ghost" id="cfg-cancel">Cancelar</button>
          </div>
        </form>
        <div id="cfg-notify" style="margin-top:14px"></div>
      </div>`;

    const offTags = initTagsInput(document.getElementById('cfg-off-domains'), cfg.off_maps_to_on_domains || []);
    const expTags = initTagsInput(document.getElementById('cfg-exp-domains'), cfg.exposed_domains || []);

    document.getElementById('cfg-cancel').addEventListener('click', () => renderConfig(container));
    document.getElementById('cfg-form').addEventListener('submit', async e => {
      e.preventDefault();
      const payload = {
        host_ip:               document.getElementById('cfg-host-ip').value,
        listen_port:           Number(document.getElementById('cfg-port').value),
        expose_by_default:     document.getElementById('cfg-expose-default').checked,
        upnp_bind_multicast:   document.getElementById('cfg-upnp').checked,
        off_maps_to_on_domains: offTags.getValues(),
        exposed_domains:        expTags.getValues(),
      };
      window.__hueApp.showLoading();
      try {
        await apiFetch('/api/config', { method:'PUT', body: JSON.stringify(payload) });
        document.getElementById('cfg-notify').innerHTML = `<div class="notify-bar success">&#10003; Configuração salva com sucesso!</div>`;
        toast('Configuração salva!', 'success');
      } catch(err) {
        document.getElementById('cfg-notify').innerHTML = `<div class="notify-bar error">${escapeHtml(err.message)}</div>`;
      } finally { window.__hueApp.hideLoading(); }
    });
  } catch(e) {
    container.innerHTML = `<div class="notify-bar error">Erro ao carregar configuração: ${escapeHtml(e.message)}</div>`;
  }
}
