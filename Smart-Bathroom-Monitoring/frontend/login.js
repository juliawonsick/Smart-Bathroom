async function doLogin() {
  const identifier = document.getElementById('identifier').value.trim();
  const password   = document.getElementById('password').value.trim();
  const err        = document.getElementById('err');

  err.style.display = 'none';
  if (!identifier || !password) return showErr(err, 'Preencha todos os campos.');

  const res  = await fetch('/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ identifier, password }) });
  const data = await res.json();

  if (data.ok) window.location.href = data.role === 'aluno' ? '/aluno' : '/limpeza';
  else showErr(err, data.msg);
}

function showErr(el, msg) { el.textContent = msg; el.style.display = 'block'; }

document.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
