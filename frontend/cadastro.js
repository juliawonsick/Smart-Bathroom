function syncRA() {
  const ra    = document.getElementById('ra').value.trim();
  const hint  = document.getElementById('ra-hint');
  const email = document.getElementById('email');
  const valid = /^\d{7}$/.test(ra);
  email.value    = valid ? `${ra}@atitus.edu.br` : '';
  hint.textContent = valid ? '✓ RA válido' : 'Apenas 7 números.';
  hint.className   = 'field-hint' + (valid ? ' valid' : '');
}

function checkPwd() {
  const len  = document.getElementById('password').value.length;
  const hint = document.getElementById('pwd-hint');
  hint.textContent = len >= 8 ? '✓ Tamanho OK' : 'Mínimo 8 caracteres.';
  hint.className   = 'field-hint' + (len >= 8 ? ' valid' : '');
}

function hasEmoji(s) { return /[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}]/u.test(s); }

async function doRegister() {
  const fields = ['name', 'ra', 'email', 'password'].map(id => document.getElementById(id).value.trim());
  const [name, ra, email, password] = fields;
  const err = document.getElementById('err');
  const ok  = document.getElementById('ok');
  err.style.display = ok.style.display = 'none';

  if (fields.some(f => !f))          return show(err, 'Preencha todos os campos.');
  if (fields.some(hasEmoji))         return show(err, 'Emojis não são permitidos.');
  if (!/^\d{7}$/.test(ra))           return show(err, 'RA deve ter exatamente 7 números.');
  if (password.length < 8)           return show(err, 'Senha deve ter ao menos 8 caracteres.');

  const res  = await fetch('/cadastro', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, ra, email, password }) });
  const data = await res.json();

  if (data.ok) {
    show(ok, 'Conta criada! Redirecionando…');
    setTimeout(() => window.location.href = '/login', 1800);
  } else {
    show(err, data.msg);
  }
}

function show(el, msg) { el.textContent = msg; el.style.display = 'block'; }

document.addEventListener('keydown', e => { if (e.key === 'Enter') doRegister(); });
