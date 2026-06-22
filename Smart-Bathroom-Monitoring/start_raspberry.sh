#!/bin/bash
# ============================================================
#  start_raspberry.sh — Ponte Arduino → Flask (Raspberry Pi 4)
#  Execute: bash start_raspberry.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

# Cria .env se ainda não existir
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[SETUP] Criando .env a partir do exemplo..."
    cp .env.example .env
    echo "[AVISO] Edite o .env e configure SERVER_URL com o IP da máquina Windows."
    echo "        Exemplo: SERVER_URL=http://192.168.1.100:5000"
    echo ""
fi

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "[SETUP] Criando ambiente virtual Python..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "[SETUP] Verificando dependências..."
pip install -r requirements.txt -q --disable-pip-version-check

echo ""
echo "============================================================"
echo "  SmartBathroom — Raspberry Pi 4"
echo "  Ponte Arduino → Servidor Flask"
echo "============================================================"
echo ""

python3 arduino_raspberry.py
