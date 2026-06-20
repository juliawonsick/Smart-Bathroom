import io
import os
import sys
import threading
import time

# Garante que o terminal suporte UTF-8 
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Carrega variáveis do arquivo .env 
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import app, init_db

DISABLE_BRIDGE = os.environ.get('DISABLE_ARDUINO_BRIDGE', '0') == '1'

try:
    from pyngrok import ngrok, conf
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False


def start_ngrok(port):
    token = os.environ.get('NGROK_AUTHTOKEN', '')
    conf.get_default().auth_token = token
    try:
        tunnel = ngrok.connect(port)
        print("\n" + "=" * 55)
        print(f"  URL PUBLICA (ngrok): {tunnel.public_url}")
        print(f"  URL LOCAL:           http://localhost:{port}")
        print("=" * 55 + "\n")
    except Exception as e:
        print(f"[NGROK ERRO] {e}")
        print(f"[INFO] Rodando apenas local em http://localhost:{port}\n")


def start_arduino_bridge():
    """Sobe a ponte serial Arduino<->Flask numa thread, sem travar o Flask."""
    try:
        from arduino_raspberry import run_bridge
    except ImportError as e:
        print(f"[AVISO] Não foi possível importar arduino_raspberry.py: {e}")
        print("[INFO]  Verifique se 'pyserial' está instalado (pip install -r requirements.txt).")
        return
    thread = threading.Thread(target=run_bridge, daemon=True)
    thread.start()


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))

    print("[DB] Inicializando banco de dados SQLite...")
    init_db()
    print("[DB] OK! Banco pronto.\n")

    print("[CONTAS PADRAO]")
    print("  Limpeza  -> usuario: limpeza.atitus | senha: limpeza2026")
    print("  Aluno    -> cadastre pelo /cadastro\n")

    if DISABLE_BRIDGE:
        print("[INFO] Ponte Arduino desabilitada (DISABLE_ARDUINO_BRIDGE=1).\n")
    else:
        print("[ARDUINO] Iniciando ponte serial em segundo plano...")
        start_arduino_bridge()

    token = os.environ.get('NGROK_AUTHTOKEN', '')
    if NGROK_AVAILABLE and token:
        print("[NGROK] Token encontrado, abrindo túnel público...")
        t = threading.Thread(target=start_ngrok, args=(PORT,), daemon=True)
        t.start()
        time.sleep(2)
    elif token and not NGROK_AVAILABLE:
        print("[AVISO] NGROK_AUTHTOKEN definido mas pyngrok não está instalado.")
        print("        Rode: pip install pyngrok\n")

    print(f"[INFO] Servidor rodando em http://0.0.0.0:{PORT}")
    print("[INFO] Acesse pelo navegador usando o IP da Raspberry na rede do campus.\n")

    app.run(debug=False, host='0.0.0.0', port=PORT, use_reloader=False)
