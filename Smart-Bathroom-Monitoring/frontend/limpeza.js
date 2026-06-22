const ITEMS = {
  'Papel Higiênico': 'ph',
  'Papel Toalha':    'pt',
  'Sabão Líquido':   'sl',
};

let currentBathroom = '';
let allBathrooms    = [];
let summaryData     = {};

const isMasc = n => n.toLowerCase().includes('masculino');

function renderTabs() {
  document.getElementById('bathroom-tabs').innerHTML = allBathrooms.map(b => {
    const cls = b === currentBathroom ? (isMasc(b) ? 'masc' : 'fem') : '';
    const dot = (summaryData[b] || 0) > 0 ? '<span class="btab-dot visible"></span>' : '';
    return `<button class="btab ${cls}" onclick="switchBathroom('${b}')">${isMasc(b) ? '🚹' : '🚺'} ${b} ${dot}</button>`;
  }).join('');
}

function renderSidebar() {
  const total = Object.values(summaryData).reduce((a, b) => a + b, 0);
  const badge = document.getElementById('nav-badge');
  badge.textContent = total;
  badge.className   = 'nav-badge' + (total > 0 ? ' visible' : '');

  document.getElementById('sidebar-bath-list').innerHTML = allBathrooms.map(b => {
    const cnt   = summaryData[b] || 0;
    const cls   = [b === currentBathroom ? 'active' : '', cnt > 0 ? 'has-alert' : ''].join(' ');
    return `<div class="sb-item ${cls}" onclick="switchBathroom('${b}')">
              <span>${isMasc(b) ? '🚹' : '🚺'} ${b}</span>
              <span class="sb-count ${cnt > 0 ? 'visible' : ''}">${cnt}</span>
            </div>`;
  }).join('');
}

function switchBathroom(b) { currentBathroom = b; renderTabs(); renderSidebar(); loadStatus(); }

async function loadStatus() {
  const data = await fetch('/api/limpeza/status?bathroom=' + encodeURIComponent(currentBathroom)).then(r => r.json());

  if (!allBathrooms.length) {
    allBathrooms    = data.bathrooms || [];
    currentBathroom = allBathrooms[0] || '';
  }
  summaryData = data.summary || {};
  renderTabs(); renderSidebar();

  document.getElementById('stat-bathroom').textContent = currentBathroom;
  document.getElementById('open-count').textContent    = data.open_count;
  document.getElementById('items-missing').textContent = data.items_missing;
  document.getElementById('last-update').textContent   = data.last_update;

  const anyMissing = Object.values(data.status).some(v => v === 'Em falta');
  document.getElementById('badge-global').innerHTML =
    `<span class="badge ${anyMissing ? 'warn' : 'ok'}">${anyMissing ? '⚠ Reposição necessária' : '✓ Tudo disponível'}</span>`;

  for (const [item, key] of Object.entries(ITEMS)) {
    const miss = data.status[item] === 'Em falta';
    const cls  = miss ? 'missing' : 'ok';
    document.getElementById(`card-${key}`).className   = `item-card ${cls}`;
    document.getElementById(`dot-${key}`).className    = `item-dot ${cls}`;
    const s = document.getElementById(`status-${key}`);
    s.className   = `item-status ${cls}`;
    s.textContent = data.status[item];
  }

  renderAlerts(data.alerts || []);
}

function renderAlerts(alerts) {
  const list  = document.getElementById('alerts-list');
  const count = document.getElementById('alerts-count');
  if (!alerts.length) {
    list.innerHTML = '<div class="alert-empty">Nenhum alerta registrado ainda.</div>';
    count.textContent = '';
    return;
  }
  const open = alerts.filter(a => a.status === 'aberto').length;
  count.textContent = open > 0 ? `${open} aberto${open > 1 ? 's' : ''}` : 'todos resolvidos';
  list.innerHTML = alerts.map(a => `
    <div class="alert-row ${a.status}">
      <div class="alert-info">
        <div class="alert-item">${a.item}</div>
        <div class="alert-meta">${a.bathroom}</div>
        <div class="alert-origin">👤 ${a.origin_user || '—'}</div>
        <div class="alert-meta">${a.created_at}${a.resolved_at ? ' · Resolvido: ' + a.resolved_at : ''}</div>
        <span class="alert-tag ${a.status}">${a.status}</span>
      </div>
      ${a.status === 'aberto' ? `<button class="btn-resolve" onclick="resolve(${a.id})">Resolver</button>` : ''}
    </div>`).join('');
}

async function resolve(id) {
  await fetch('/api/limpeza/resolve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
  loadStatus();
}

async function markCleaning() {
  const msg = document.getElementById('clean-msg');
  await fetch('/api/limpeza/mark_cleaning', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ bathroom: currentBathroom }) });
  msg.textContent = `✓ ${currentBathroom} marcado como realizado.`;
  msg.style.display = 'block';
  loadStatus();
  setTimeout(() => msg.style.display = 'none', 6000);
}

fetch('/api/limpeza/status').then(r => r.json()).then(d => {
  allBathrooms    = d.bathrooms || [];
  currentBathroom = allBathrooms[0] || '';
  summaryData     = d.summary   || {};
  renderTabs(); renderSidebar(); loadStatus();
});

setInterval(loadStatus, 6000);
