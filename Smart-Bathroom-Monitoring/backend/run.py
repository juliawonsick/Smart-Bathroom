# -*- coding: utf-8 -*-
"""
run.py - Inicia o SmartBathroom com Flask + ngrok
Execute: python run.py
"""

import io
import os
import sys
import threading
import time

# Garante que o terminal Windows suporte UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Carrega variáveis do arquivo .env (se existir)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Tenta importar pyngrok
try:
    from pyngrok import ngrok, conf
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("[AVISO] pyngrok nao instalado. Rode: pip install pyngrok")
    print("[INFO]  Continuando sem ngrok - acesso apenas local.\n")

from app import app, init_db

def start_ngrok(port=5000):
    token = os.environ.get('NGROK_AUTHTOKEN', '')
    if token:
        conf.get_default().auth_token = token

    try:
        tunnel = ngrok.connect(port)
        public_url = tunnel.public_url
        print("\n" + "="*55)
        print(f"  URL PUBLICA (ngrok): {public_url}")
        print(f"  URL LOCAL:           http://localhost:{port}")
        print("="*55)
        print("  Acesse qualquer um dos enderecos acima no navegador.")
        print("  Use a URL publica para testar em outros dispositivos.")
        print("="*55 + "\n")
        return public_url
    except Exception as e:
        print(f"[NGROK ERRO] {e}")
        print(f"[INFO] Rodando apenas local em http://localhost:{port}\n")
        return None

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))

    print("[DB] Inicializando banco de dados SQLite...")
    init_db()
    print("[DB] OK! Banco pronto.\n")

    print("[CONTAS PADRAO]")
    print("  Limpeza  -> usuario: limpeza.atitus | senha: limpeza2026")
    print("  Aluno    -> cadastre pelo /cadastro\n")

    if NGROK_AVAILABLE:
        token = os.environ.get('NGROK_AUTHTOKEN', '')
        if token:
            t = threading.Thread(target=start_ngrok, args=(PORT,), daemon=True)
            t.start()
            time.sleep(2)
        else:
            print("[INFO] NGROK_AUTHTOKEN nao configurado - rodando apenas local.")
            print(f"[INFO] Acesse: http://localhost:{PORT}\n")
    else:
        print(f"[INFO] Servidor rodando em http://localhost:{PORT}\n")

    app.run(debug=False, host='0.0.0.0', port=PORT, use_reloader=False)
