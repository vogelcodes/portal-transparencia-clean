import os
import time
import random
import logging
import requests
from datetime import datetime

from src.rate_limit import wait_for_quota

logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY_PORTAL")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "chave-api-dados": API_KEY
}


def _exp_backoff(attempt):
    return min(60.0, 2 ** attempt) + random.uniform(0, 1)


def _parse_retry_after(header):
    try:
        return float(header) if header else 0.0
    except (ValueError, TypeError):
        return 0.0


def request_portal(url, params=None, max_retries=5):
    for attempt in range(max_retries):
        wait_for_quota()
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        except requests.exceptions.RequestException as exc:
            logger.warning("request_portal network error attempt=%d: %s", attempt, exc)
            if attempt < max_retries - 1:
                time.sleep(_exp_backoff(attempt))
                continue
            raise

        if r.status_code == 200:
            return r

        if r.status_code == 429:
            backoff = max(_parse_retry_after(r.headers.get("Retry-After")), _exp_backoff(attempt))
            logger.warning("429 received, backoff=%.1fs attempt=%d", backoff, attempt)
            time.sleep(backoff)
            continue

        if 500 <= r.status_code < 600:
            backoff = _exp_backoff(attempt)
            logger.warning("5xx status=%d backoff=%.1fs attempt=%d", r.status_code, backoff, attempt)
            time.sleep(backoff)
            continue

        r.raise_for_status()

    raise RuntimeError(f"request_portal failed after {max_retries} retries: {url}")


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
    while True:
        try:
            r = request_portal(url, params=params)
            data = r.json()
            if not data:
                break
            all_data.extend(data)
            params['pagina'] += 1
            if len(data) < 15:
                break
        except Exception:
            break
    return all_data


def get_empenho_details(doc_id):
    url = f"https://api.portaldatransparencia.gov.br/api-de-dados/despesas/documentos/{doc_id}"
    try:
        return request_portal(url).json()
    except Exception:
        return {}


def get_itens_empenho(doc_id):
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/despesas/itens-de-empenho"
    try:
        data = request_portal(url, params={"codigoDocumento": doc_id, "pagina": 1}).json()
        return sorted(data, key=lambda x: int(x.get('sequencial', 0)))
    except Exception:
        return []


def get_item_historico(doc_id, sequencial):
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/despesas/itens-de-empenho/historico"
    try:
        return request_portal(url, params={"codigoDocumento": doc_id, "sequencial": sequencial, "pagina": 1}).json()
    except Exception:
        return []


def get_documentos_relacionados(doc_id):
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/despesas/documentos-relacionados"
    try:
        return request_portal(url, params={"codigoDocumento": doc_id, "fase": 1}).json()
    except Exception:
        return []


def get_empresa(cnpj):
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/pessoa-juridica"
    clean = cnpj.replace('.', '').replace('/', '').replace('-', '')
    try:
        return request_portal(url, params={"cnpj": clean}).json()
    except Exception:
        return {}
