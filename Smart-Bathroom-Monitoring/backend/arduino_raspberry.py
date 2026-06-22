import json
import logging
import os
import time

import requests
import serial
import serial.tools.list_ports

# Carrega variáveis do arquivo .env (se existir)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# CONFIGURAÇÃO — sobrescrevível via variáveis de ambiente / arquivo .env
SERVER_URL  = os.environ.get("SERVER_URL",  "http://localhost:5000")
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyUSB0")   # Linux (Raspberry Pi)
SERIAL_BAUD = int(os.environ.get("SERIAL_BAUD", "9600"))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", "5"))

# Mapeamento das chaves do Arduino para os nomes da API
BATH_MAP = {
    "masc": "Banheiro Bloco A - Masculino",
    "fem":  "Banheiro Bloco A - Feminino",
}
ITEM_MAP = {
    "ph":  "Papel Higiênico",
    "sab": "Sabão Líquido",
}

# LOGGING CONFIG
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
log = logging.getLogger(__name__)


# FUNÇÕES

def encontrar_arduino() -> str:
    for port in serial.tools.list_ports.comports():
        if any(d in port.description for d in ("Arduino", "CH340", "CH341", "USB Serial", "ACM")):
            log.info(f"Arduino encontrado em {port.device} ({port.description})")
            return port.device
    return SERIAL_PORT


def reportar_falta(item: str, bathroom: str) -> None:
    try:
        resp = requests.post(
            f"{SERVER_URL}/api/arduino/report",
            json={"item": item, "bathroom": bathroom},
            timeout=5,
        )
        data = resp.json()
        if data.get("ok"):
            log.info(f"[ALERTA CRIADO] {item} em '{bathroom}'")
        else:
            log.warning(f"[ALERTA JA EXISTE] {item} em '{bathroom}' – {data.get('msg','')}")
    except requests.RequestException as e:
        log.error(f"Erro ao reportar falta: {e}")


def resolver_banheiro(bathroom: str) -> None:
    try:
        resp = requests.post(
            f"{SERVER_URL}/api/arduino/resolve",
            json={"bathroom": bathroom},
            timeout=5,
        )
        data = resp.json()
        if data.get("ok"):
            log.info(f"[RESOLVIDO] Alertas de '{bathroom}' encerrados via sala de limpeza")
        else:
            log.warning(f"[RESOLVE ERRO] {data.get('msg','')}")
    except requests.RequestException as e:
        log.error(f"Erro ao resolver banheiro: {e}")


def processar(dados: dict) -> None:
    evento = dados.get("event")
    tipo   = dados.get("type")

    if evento == "alert":
        bathroom = BATH_MAP.get(dados.get("bathroom", ""))
        item     = ITEM_MAP.get(dados.get("item", ""))
        if bathroom and item:
            log.warning(f"[BOTÃO] {item} faltando em '{bathroom}'")
            reportar_falta(item, bathroom)
        else:
            log.warning(f"Evento de alerta com dados inválidos: {dados}")

    elif evento == "resolve":
        bathroom = BATH_MAP.get(dados.get("bathroom", ""))
        if bathroom:
            log.info(f"[BOTÃO LIMPEZA] Resolvendo '{bathroom}'")
            resolver_banheiro(bathroom)

    elif tipo == "status":
        log.debug(f"Status periódico: {dados}")

    elif dados.get("status") == "iniciado":
        log.info("Arduino (re)iniciado.")


# LOOP PRINCIPAL

def main() -> None:
    log.info("=" * 55)
    log.info("  SmartBathroom – Raspberry Pi 4")
    log.info(f"  Servidor : {SERVER_URL}")
    log.info("=" * 55)

    while True:
        porta = encontrar_arduino()
        log.info(f"Conectando ao Arduino em {porta} ({SERIAL_BAUD} baud)...")

        try:
            with serial.Serial(porta, SERIAL_BAUD, timeout=2) as ser:
                log.info("Arduino conectado! Aguardando eventos...\n")

                while True:
                    linha = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not linha:
                        continue

                    try:
                        dados = json.loads(linha)
                    except json.JSONDecodeError:
                        log.debug(f"Ignorado: {linha}")
                        continue

                    processar(dados)

        except serial.SerialException as e:
            log.error(f"Erro serial: {e}")
            log.info(f"Reconectando em {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

        except Exception as e:
            log.error(f"Erro inesperado: {e}")
            time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    main()
