from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import hashlib
import re
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, '..', 'frontend'))
app.secret_key = os.environ.get('SECRET_KEY', 'smartbathroom_secret_key_2026')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.permanent_session_lifetime = timedelta(hours=12)   # <- aqui
CORS(app)

DB_PATH = os.path.join(BASE_DIR, 'smartbathroom.db')

BATHROOMS = [
    'Banheiro Bloco A - Masculino',
    'Banheiro Bloco A - Feminino',
]
ITEMS = ['Papel Higiênico', 'Sabão Líquido']

# DB 

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        ra TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'aluno'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bathroom TEXT,
        item TEXT,
        origin_user TEXT,
        origin_ra TEXT,
        origin_id INTEGER,
        status TEXT DEFAULT 'aberto',
        created_at TEXT,
        resolved_at TEXT
    )''')
    try:
        c.execute("ALTER TABLE alerts ADD COLUMN origin_ra TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN bathroom TEXT")
    except Exception:
        pass

    pwd = hashlib.sha256('limpeza2026'.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (name, ra, email, password, role) VALUES (?,?,?,?,?)",
              ('Equipe de Limpeza', 'limpeza', 'limpeza.atitus', pwd, 'limpeza'))
    conn.commit()
    conn.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def contains_emoji(text):
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]+",
        flags=re.UNICODE)
    return bool(emoji_pattern.search(text))

# AUTH 

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'aluno':   return redirect(url_for('aluno_dashboard'))
        if role == 'limpeza': return redirect(url_for('limpeza_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        identifier = data.get('identifier', '').strip()
        password   = data.get('password',   '').strip()
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE (ra=? OR email=?) AND password=?",
            (identifier, identifier, hash_pw(password))
        ).fetchone()
        conn.close()
        if user:
            session.permanent    = True
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['user_ra']   = user['ra']
            session['role']      = user['role']
            session['bathroom']  = user['bathroom'] or BATHROOMS[0]
            return jsonify({'ok': True, 'role': user['role']})
        return jsonify({'ok': False, 'msg': 'Usuário ou senha inválidos.'})
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        data     = request.get_json()
        name     = data.get('name',     '').strip()
        ra       = data.get('ra',       '').strip()
        email    = data.get('email',    '').strip()
        password = data.get('password', '').strip()
        bathroom = data.get('bathroom', '').strip()
        for field in [name, ra, email, password]:
            if contains_emoji(field):
                return jsonify({'ok': False, 'msg': 'Emojis não são permitidos nos campos.'})
        if not re.match(r'^\d{7}$', ra):
            return jsonify({'ok': False, 'msg': 'RA deve ter exatamente 7 números.'})
        if email.lower() != f"{ra}@atitus.edu.br":
            return jsonify({'ok': False, 'msg': f'Email deve ser {ra}@atitus.edu.br'})
        if len(password) < 8:
            return jsonify({'ok': False, 'msg': 'A senha deve ter pelo menos 8 caracteres.'})
        if len(name) < 3:
            return jsonify({'ok': False, 'msg': 'Nome completo é obrigatório.'})
        if bathroom not in BATHROOMS:
            return jsonify({'ok': False, 'msg': 'Selecione um banheiro válido.'})
        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (name, ra, email, password, role, bathroom) VALUES (?,?,?,?,?,?)",
                (name, ra, email.lower(), hash_pw(password), 'aluno', bathroom)
            )
            conn.commit()
            conn.close()
            return jsonify({'ok': True})
        except sqlite3.IntegrityError:
            return jsonify({'ok': False, 'msg': 'RA ou email já cadastrado.'})
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ALUNO

@app.route('/aluno')
def aluno_dashboard():
    if 'user_id' not in session or session.get('role') != 'aluno':
        return redirect(url_for('login'))
    return render_template('aluno.html', user_name=session['user_name'], bathroom=session.get('bathroom', BATHROOMS[0]))

@app.route('/api/aluno/status')
def aluno_status():
    bathroom = session.get('bathroom', BATHROOMS[0])
    conn = get_db()
    status = {}
    for item in ITEMS:
        alert = conn.execute(
            "SELECT * FROM alerts WHERE item=? AND bathroom=? AND status='aberto' ORDER BY created_at DESC LIMIT 1",
            (item, bathroom)
        ).fetchone()
        status[item] = 'Em falta' if alert else 'Disponível'
    total_open = conn.execute(
        "SELECT COUNT(*) as cnt FROM alerts WHERE bathroom=? AND status='aberto'", (bathroom,)
    ).fetchone()['cnt']
    conn.close()
    return jsonify({
        'status': status,
        'open_count': total_open,
        'items_missing': sum(1 for v in status.values() if v == 'Em falta'),
        'last_update': datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
        'bathrooms': BATHROOMS,
    })

@app.route('/api/aluno/report', methods=['POST'])
def aluno_report():
    if 'user_id' not in session:
        return jsonify({'ok': False, 'msg': 'Não autorizado'})
    data     = request.get_json()
    item     = data.get('item')
    bathroom = session.get('bathroom', BATHROOMS[0])
    if item not in ITEMS:
        return jsonify({'ok': False, 'msg': 'Item inválido'})
    if bathroom not in BATHROOMS:
        return jsonify({'ok': False, 'msg': 'Banheiro inválido'})
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM alerts WHERE item=? AND bathroom=? AND status='aberto'",
        (item, bathroom)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({'ok': False, 'msg': f'Já existe um alerta aberto para {item}.'})
    origin_label = f"{session['user_name']} (RA: {session.get('user_ra','')})"
    conn.execute(
        "INSERT INTO alerts (bathroom, item, origin_user, origin_ra, origin_id, status, created_at) VALUES (?,?,?,?,?,?,?)",
        (bathroom, item, origin_label, session.get('user_ra',''), session['user_id'], 'aberto',
         datetime.now().strftime('%d/%m/%Y, %H:%M:%S'))
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# LIMPEZA

@app.route('/limpeza')
def limpeza_dashboard():
    if 'user_id' not in session or session.get('role') != 'limpeza':
        return redirect(url_for('login'))
    return render_template('limpeza.html', user_name=session['user_name'])

@app.route('/api/limpeza/status')
def limpeza_status():
    bathroom = request.args.get('bathroom', BATHROOMS[0])
    conn = get_db()
    status = {}
    for item in ITEMS:
        alert = conn.execute(
            "SELECT * FROM alerts WHERE item=? AND bathroom=? AND status='aberto' ORDER BY created_at DESC LIMIT 1",
            (item, bathroom)
        ).fetchone()
        status[item] = 'Em falta' if alert else 'Disponível'
    total_open = conn.execute(
        "SELECT COUNT(*) as cnt FROM alerts WHERE bathroom=? AND status='aberto'", (bathroom,)
    ).fetchone()['cnt']
    alerts = conn.execute(
        "SELECT * FROM alerts WHERE bathroom=? ORDER BY created_at DESC LIMIT 30", (bathroom,)
    ).fetchall()
    summary = {}
    for b in BATHROOMS:
        cnt = conn.execute(
            "SELECT COUNT(*) as cnt FROM alerts WHERE bathroom=? AND status='aberto'", (b,)
        ).fetchone()['cnt']
        summary[b] = cnt
    conn.close()
    return jsonify({
        'status': status,
        'open_count': total_open,
        'items_missing': sum(1 for v in status.values() if v == 'Em falta'),
        'last_update': datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
        'alerts': [dict(a) for a in alerts],
        'bathrooms': BATHROOMS,
        'summary': summary,
    })

@app.route('/api/limpeza/resolve', methods=['POST'])
def limpeza_resolve():
    if 'user_id' not in session or session.get('role') != 'limpeza':
        return jsonify({'ok': False})
    data = request.get_json()
    alert_id = data.get('id')
    conn = get_db()
    conn.execute(
        "UPDATE alerts SET status='resolvido', resolved_at=? WHERE id=?",
        (datetime.now().strftime('%d/%m/%Y, %H:%M:%S'), alert_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/limpeza/mark_cleaning', methods=['POST'])
def mark_cleaning():
    if 'user_id' not in session or session.get('role') != 'limpeza':
        return jsonify({'ok': False})
    data     = request.get_json()
    bathroom = data.get('bathroom', BATHROOMS[0])
    conn = get_db()
    conn.execute(
        "UPDATE alerts SET status='resolvido', resolved_at=? WHERE bathroom=? AND status='aberto'",
        (datetime.now().strftime('%d/%m/%Y, %H:%M:%S'), bathroom)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ARDUINO/RASPBERRY

@app.route('/api/arduino/report', methods=['POST'])
def arduino_report():
    data     = request.get_json()
    item     = data.get('item')
    bathroom = data.get('bathroom', BATHROOMS[0])
    if item not in ITEMS:
        return jsonify({'ok': False, 'msg': 'Item inválido'})
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM alerts WHERE item=? AND bathroom=? AND status='aberto'",
        (item, bathroom)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({'ok': False, 'msg': 'Alerta já existe'})
    conn.execute(
        "INSERT INTO alerts (bathroom, item, origin_user, origin_ra, origin_id, status, created_at) VALUES (?,?,?,?,?,?,?)",
        (bathroom, item, 'Sensor Automático', 'arduino', 0, 'aberto',
         datetime.now().strftime('%d/%m/%Y, %H:%M:%S'))
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/arduino/resolve', methods=['POST'])
def arduino_resolve():
    data     = request.get_json()
    bathroom = data.get('bathroom', '')
    if bathroom not in BATHROOMS:
        return jsonify({'ok': False, 'msg': 'Banheiro inválido'})
    conn = get_db()
    conn.execute(
        "UPDATE alerts SET status='resolvido', resolved_at=? WHERE bathroom=? AND status='aberto'",
        (datetime.now().strftime('%d/%m/%Y, %H:%M:%S'), bathroom)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/arduino/status', methods=['GET'])
def arduino_status():
    bathroom = request.args.get('bathroom', BATHROOMS[0])
    conn = get_db()
    status = {}
    for item in ITEMS:
        alert = conn.execute(
            "SELECT * FROM alerts WHERE item=? AND bathroom=? AND status='aberto'",
            (item, bathroom)
        ).fetchone()
        status[item] = 'falta' if alert else 'ok'
    conn.close()
    return jsonify(status)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)