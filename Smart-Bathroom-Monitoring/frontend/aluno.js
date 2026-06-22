const ITEMS = {
  'Papel Higiênico': 'ph',
  'Papel Toalha':    'pt',
  'Sabão Líquido':   'sl',
};

let currentBathroom = '';
let allBathrooms    = [];

const isMasc = n => n.toLowerCase().includes('masculino');

function renderTabs() {
  document.getElementById('bathroom-tabs').innerHTML = allBathrooms.map(b => {
    const cls = b === currentBathroom ? (isMasc(b) ? 'masc' : 'fem') : '';
    return `<button class="btab ${cls}" onclick="switchBathroom('${b}')">${isMasc(b) ? '🚹' : '🚺'} ${b}</button>`;
  }).join('');
}

function switchBathroom(b) { currentBathroom = b; renderTabs(); loadStatus(); }

async function loadStatus() {
  const data = await fetch('/api/aluno/status?bathroom=' + encodeURIComponent(currentBathroom)).then(r => r.json());

  if (!allBathrooms.length) {
    allBathrooms = data.bathrooms || [];
    currentBathroom = allBathrooms[0] || '';
    renderTabs();
  }

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
}

async function report(item) {
  const msg  = document.getElementById('report-msg');
  const data = await fetch('/api/aluno/report', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item, bathroom: currentBathroom }),
  }).then(r => r.json());

  msg.className = 'report-msg ' + (data.ok ? 'ok' : 'err');
  msg.textContent = data.ok ? `✓ Alerta registrado: ${item}` : data.msg;
  msg.style.display = 'block';
  loadStatus();
  setTimeout(() => msg.style.display = 'none', 5000);
}

fetch('/api/aluno/status').then(r => r.json()).then(d => {
  allBathrooms    = d.bathrooms || [];
  currentBathroom = allBathrooms[0] || '';
  renderTabs(); loadStatus();
});

setInterval(loadStatus, 8000);
