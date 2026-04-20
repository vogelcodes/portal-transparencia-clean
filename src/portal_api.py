import os
import time
import requests
from datetime import datetime

API_KEY = os.getenv("API_KEY_PORTAL")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "chave-api-dados": API_KEY
}

LIMIT_DAY = 400
LIMIT_NIGHT = 700
NIGHT_START = 0
NIGHT_END = 6


def get_rate_limit_delay():
    hour = datetime.now().hour
    if NIGHT_START <= hour < NIGHT_END:
        return (60.0 / LIMIT_NIGHT) * 1.1
    return (60.0 / LIMIT_DAY) * 1.1


def format_currency(value):
    try:
        if isinstance(value, str):
            value = float(value.replace('.', '').replace(',', '.'))
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"R$ {value}"


def format_date(date_str):
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').strftime('%d/%m/%Y')
    except Exception:
        return date_str


def get_empenhos_list(cnpj, year):
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/despesas/documentos-por-favorecido"
    params = {
        "codigoPessoa": cnpj.replace('.', '').replace('/', '').replace('-', ''),
        "ano": year,
        "fase": 1,
        "pagina": 1
    }
    all_data = []
    retries = 0
    while True:
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                if retries < 3:
                    retries += 1
                    time.sleep(1)
                    continue
                break
            data = r.json()
            if not data:
                break
            all_data.extend(data)
            params['pagina'] += 1
            retries = 0
            if len(data) < 15:
                break
            time.sleep(get_rate_limit_delay())
        except Exception:
            if retries < 3:
                retries += 1
                time.sleep(1)
                continue
            break
    return all_data


def get_empenho_details(doc_id):
    url = f"https://api.portaldatransparencia.gov.br/api-de-dados/despesas/documentos/{doc_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        time.sleep(get_rate_limit_delay())
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}
