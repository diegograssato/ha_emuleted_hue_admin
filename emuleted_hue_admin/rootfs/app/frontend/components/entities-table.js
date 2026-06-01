import { apiFetch, escapeHtml, toast } from './utils.js';

let _state = { page: 1, per_page: 25, search: '', hidden: '', domain: '' };
let _total = 0;
let _editingId = null;

// Cache of HA states loaded once per session: Map<entity_id, friendly_name>
let _haStates = null;

export function renderEntities(container) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title">Busca e Listagem de Entidades</div>
      <div class="filter-bar">
        <button class="btn btn-primary" id="ent-new">&#43; Nova Entidade</button>
        <button class="btn btn-ghost"   id="ent-export">&#8659; Exportar YAML</button>
        <button class="btn btn-ghost"   id="ent-import-btn">&#8657; Importar YAML</button>
      </div>
      <div class="filter-bar">
        <div class="form-group grow"><label>Busca</label><input type="text" id="ent-search" placeholder="entity_id ou nome... (ex: switch.sala)" /></div>
        <div class="form-group"><label>Domínio</label>
          <select id="ent-domain">
            <option value="">Todos</option>
            <option value="light">light</option>
            <option value="switch">switch</option>
            <option value="scene">scene</option>
            <option value="script">script</option>
            <option value="media_player">media_player</option>
            <option value="fan">fan</option>
            <option value="cover">cover</option>
            <option value="climate">climate</option>
            <option value="group">group</option>
          </select>
        </div>
        <div class="form-group"><label>Ocultas</label>
          <select id="ent-hidden">
            <option value="">Todas</option>
            <option value="false">Visíveis</option>
            <option value="true">Ocultas</option>
          </select>
        </div>
        <div style="display:flex;gap:6px;align-items:flex-end">
          <button class="btn btn-primary" id="ent-buscar">Buscar</button>
          <button class="btn btn-ghost"   id="ent-limpar">Limpar</button>
        </div>
      </div>
      <div id="ent-table-area"></div>
      <div class="pagination" id="ent-pagination"></div>
    </div>

    <!-- Import modal -->
    <div id="import-modal" class="modal hidden">
      <div class="modal-backdrop" id="import-backdrop"></div>
      <div class="modal-box">
        <h2 class="modal-title">Importar Entidades (YAML)</h2>
        <div class="form-group" style="margin-bottom:12px">
          <label>Cole o YAML abaixo</label>
          <textarea id="import-yaml" class="yaml-textarea" style="min-height:200px" placeholder="light.sala:\n  name: Sala\n  hidden: false"></textarea>
        </div>
        <div id="import-error"></div>
        <div class="modal-actions">
          <button class="btn btn-ghost" id="import-cancel">Cancelar</button>
          <button class="btn btn-primary" id="import-submit">Importar</button>
        </div>
      </div>
    </div>`;

  document.getElementById('ent-buscar').addEventListener('click', () => {
    _state.search = document.getElementById('ent-search').value;
    _state.domain = document.getElementById('ent-domain').value;
    _state.hidden = document.getElementById('ent-hidden').value;
    _state.page   = 1;
    loadTable();
  });
  document.getElementById('ent-limpar').addEventListener('click', () => {
    _state = { page: 1, per_page: 25, search: '', hidden: '', domain: '' };
    document.getElementById('ent-search').value  = '';
    document.getElementById('ent-domain').value  = '';
    document.getElementById('ent-hidden').value  = '';
    loadTable();
  });
  document.getElementById('ent-search').addEventListener('keydown', e => { if (e.key === 'Enter') document.getElementById('ent-buscar').click(); });
  document.getElementById('ent-new').addEventListener('click', () => openModal(null));
  document.getElementById('ent-export').addEventListener('click', exportYaml);
  document.getElementById('ent-import-btn').addEventListener('click', () => document.getElementById('import-modal').classList.remove('hidden'));
  document.getElementById('import-cancel').addEventListener('click', () => document.getElementById('import-modal').classList.add('hidden'));
  document.getElementById('import-backdrop').addEventListener('click', () => document.getElementById('import-modal').classList.add('hidden'));
  document.getElementById('import-submit').addEventListener('click', doImport);

  loadTable();
}

async function loadTable() {
  const area = document.getElementById('ent-table-area');
  area.innerHTML = `<div class="spinner" style="margin:30px auto;display:block"></div>`;
  const params = new URLSearchParams({ page: _state.page, per_page: _state.per_page });
  if (_state.search) params.set('search', _state.search);
  if (_state.domain) params.set('domain', _state.domain);
  if (_state.hidden) params.set('hidden', _state.hidden);
  try {
    const data = await apiFetch(`/api/entities?${params}`);
    _total = data.total;
    area.innerHTML = `
      <div style="margin-bottom:10px;color:var(--text-muted);font-size:13px">Total: ${data.total}</div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>ENTITY ID</th><th>NOME</th><th>OCULTA</th><th style="text-align:right">AÇÕES</th>
          </tr></thead>
          <tbody id="ent-tbody">
            ${data.items.length === 0 ? `<tr><td colspan="4" style="text-align:center;padding:24px;color:var(--text-muted)">Nenhuma entidade encontrada.</td></tr>` :
              data.items.map(e => `
                <tr>
                  <td class="text-bright">${escapeHtml(e.entity_id)}</td>
                  <td>${escapeHtml(e.name || '—')}</td>
                  <td>${e.hidden ? '<span class="badge badge-red">Sim</span>' : '<span class="badge badge-green">Não</span>'}</td>
                  <td>
                    <div class="td-actions">
                      <button class="btn btn-ghost btn-icon" title="Editar"     data-action="edit"   data-id="${escapeHtml(e.entity_id)}">&#9998;</button>
                      <button class="btn btn-ghost btn-icon" title="Duplicar"   data-action="dup"    data-id="${escapeHtml(e.entity_id)}">&#9112;</button>
                      <button class="btn btn-danger btn-icon" title="Excluir"   data-action="del"    data-id="${escapeHtml(e.entity_id)}">&#128465;</button>
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
    area.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        if (btn.dataset.action === 'edit') openModal(id);
        if (btn.dataset.action === 'dup')  duplicateEntity(id);
        if (btn.dataset.action === 'del')  deleteEntity(id);
      });
    });
    renderPagination(data.total, data.page, data.per_page);
  } catch(e) {
    area.innerHTML = `<div class="notify-bar error">${escapeHtml(e.message)}</div>`;
  }
}

function renderPagination(total, page, per_page) {
  const pages = Math.ceil(total / per_page) || 1;
  const pag = document.getElementById('ent-pagination');
  pag.innerHTML = `
    <span>Página ${page} de ${pages}</span>
    <div class="pagination-btns">
      <button class="btn btn-ghost btn-sm" id="pag-prev" ${page<=1?'disabled':''}>Anterior</button>
      <button class="btn btn-ghost btn-sm" id="pag-next" ${page>=pages?'disabled':''}>Próxima</button>
    </div>
    <div style="display:flex;align-items:center;gap:8px">
      <span style="color:var(--text-muted)">Itens por página</span>
      <select id="pag-size" style="width:80px">
        ${[10,25,50,100].map(n=>`<option ${n===per_page?'selected':''}>${n}</option>`).join('')}
      </select>
    </div>`;
  document.getElementById('pag-prev').addEventListener('click', () => { _state.page--; loadTable(); });
  document.getElementById('pag-next').addEventListener('click', () => { _state.page++; loadTable(); });
  document.getElementById('pag-size').addEventListener('change', e => { _state.per_page = Number(e.target.value); _state.page = 1; loadTable(); });
}

function openModal(entityId) {
  _editingId = entityId;
  const modal = document.getElementById('entity-modal');
  const title = document.getElementById('entity-modal-title');
  const form  = document.getElementById('entity-form');
  form.reset();
  const entityIdInput = document.getElementById('ef-entity-id');
  entityIdInput.disabled = false;
  title.textContent = entityId ? 'Editar Entidade' : 'Nova Entidade';
  modal.classList.remove('hidden');

  if (entityId) {
    // Editing: disable entity_id field, hide autocomplete hint
    entityIdInput.disabled = true;
    _setAutocompleteHint(false);
    apiFetch(`/api/entities/${encodeURIComponent(entityId)}`).then(e => {
      entityIdInput.value = e.entity_id;
      document.getElementById('ef-name').value    = e.name || '';
      document.getElementById('ef-hidden').checked = !!e.hidden;
    });
  } else {
    // Creating: load HA states for autocomplete
    _loadHaStatesIntoDatalist();
    // Auto-fill friendly_name when user selects an entity_id
    entityIdInput.addEventListener('input', _onEntityIdInput);
  }

  document.getElementById('entity-modal-cancel').onclick = () => {
    entityIdInput.removeEventListener('input', _onEntityIdInput);
    closeModal();
  };
  document.getElementById('entity-modal-backdrop').onclick = () => {
    entityIdInput.removeEventListener('input', _onEntityIdInput);
    closeModal();
  };
  form.onsubmit = (e) => {
    entityIdInput.removeEventListener('input', _onEntityIdInput);
    saveEntity(e);
  };
}

function _setAutocompleteHint(show, text = '') {
  const hint = document.getElementById('ef-entity-id-hint');
  if (!hint) return;
  if (show) {
    hint.textContent = text;
    hint.style.display = 'block';
  } else {
    hint.style.display = 'none';
  }
}

function _onEntityIdInput() {
  if (!_haStates) return;
  const val = document.getElementById('ef-entity-id').value.trim();
  const friendly = _haStates.get(val);
  if (friendly && !document.getElementById('ef-name').value) {
    document.getElementById('ef-name').value = friendly;
  }
}

async function _loadHaStatesIntoDatalist() {
  const datalist = document.getElementById('ha-states-datalist');
  if (!datalist) return;

  // Already populated in this session
  if (_haStates !== null) {
    _renderDatalist(datalist);
    return;
  }

  _setAutocompleteHint(true, '⟳ Carregando estados do Home Assistant…');
  try {
    const states = await apiFetch('/api/entities/ha-states');
    _haStates = new Map(states.map(s => [s.entity_id, s.friendly_name || '']));
    _renderDatalist(datalist);
    _setAutocompleteHint(
      states.length > 0,
      `✓ ${states.length} entidades disponíveis — digite para filtrar`,
    );
  } catch (_) {
    _haStates = new Map();
    _setAutocompleteHint(true, '⚠ Não foi possível carregar estados do HA');
  }
}

function _renderDatalist(datalist) {
  if (!_haStates) return;
  datalist.innerHTML = '';
  for (const [entityId, friendlyName] of _haStates) {
    const opt = document.createElement('option');
    opt.value = entityId;
    opt.label = friendlyName || entityId;
    datalist.appendChild(opt);
  }
}

function closeModal() { document.getElementById('entity-modal').classList.add('hidden'); }

async function saveEntity(e) {
  e.preventDefault();
  const payload = {
    name:   document.getElementById('ef-name').value,
    hidden: document.getElementById('ef-hidden').checked,
  };
  window.__hueApp.showLoading();
  try {
    if (_editingId) {
      await apiFetch(`/api/entities/${encodeURIComponent(_editingId)}`, { method:'PUT', body: JSON.stringify(payload) });
      toast('Entidade atualizada!', 'success');
    } else {
      payload.entity_id = document.getElementById('ef-entity-id').value;
      await apiFetch('/api/entities', { method:'POST', body: JSON.stringify(payload) });
      toast('Entidade criada!', 'success');
    }
    closeModal();
    loadTable();
  } catch(err) { toast(err.message, 'error'); }
  finally { window.__hueApp.hideLoading(); }
}

async function deleteEntity(id) {
  if (!await window.__hueApp.confirm(`Excluir "${id}"?`)) return;
  window.__hueApp.showLoading();
  try {
    await apiFetch(`/api/entities/${encodeURIComponent(id)}`, { method:'DELETE' });
    toast('Entidade excluída.', 'success');
    loadTable();
  } catch(e) { toast(e.message, 'error'); }
  finally { window.__hueApp.hideLoading(); }
}

async function duplicateEntity(id) {
  const newId = prompt(`Novo Entity ID (duplicando ${id}):`, `${id}_copy`);
  if (!newId) return;
  window.__hueApp.showLoading();
  try {
    await apiFetch(`/api/entities/${encodeURIComponent(id)}/duplicate`, { method:'POST', body: JSON.stringify({ new_entity_id: newId }) });
    toast('Entidade duplicada!', 'success');
    loadTable();
  } catch(e) { toast(e.message, 'error'); }
  finally { window.__hueApp.hideLoading(); }
}

async function exportYaml() {
  window.__hueApp.showLoading();
  try {
    const text = await apiFetch('/api/entities/export');
    const blob = new Blob([text], { type: 'text/yaml' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'emulated_hue_entities.yaml'; a.click();
    URL.revokeObjectURL(url);
  } catch(e) { toast(e.message, 'error'); }
  finally { window.__hueApp.hideLoading(); }
}

async function doImport() {
  const yaml    = document.getElementById('import-yaml').value.trim();
  const errEl   = document.getElementById('import-error');
  errEl.innerHTML = '';
  if (!yaml) { errEl.innerHTML = '<div class="notify-bar error">Cole o YAML antes de importar.</div>'; return; }
  window.__hueApp.showLoading();
  try {
    await apiFetch('/api/entities/import', { method:'POST', body: JSON.stringify({ yaml_content: yaml }) });
    toast('Entidades importadas com sucesso!', 'success');
    document.getElementById('import-modal').classList.add('hidden');
    loadTable();
  } catch(e) {
    errEl.innerHTML = `<div class="notify-bar error">${escapeHtml(e.message)}</div>`;
  } finally { window.__hueApp.hideLoading(); }
}
