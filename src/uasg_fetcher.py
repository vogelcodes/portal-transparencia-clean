"""Fetch ARPs, items and empenhos from dadosabertos.compras.gov.br.

Rate limiting: the compras.gov.br public API does not publish explicit limits.
Empirically it starts returning 429 around ~200 req/min. We throttle to ~40
req/min (SLEEP=1.5s) with exponential backoff on 429/5xx and Retry-After
honored when present.
"""
import time
import random
import logging
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://dadosabertos.compras.gov.br/modulo-arp"
HEADERS = {'accept': '*/*'}
PAGE_SIZE = 500
SLEEP = 1.5
MAX_RETRIES = 6


def _exp_backoff(attempt):
    return min(60.0, 2 ** attempt) + random.uniform(0, 1)


def _parse_retry_after(header):
    try:
        return float(header) if header else 0.0
    except (ValueError, TypeError):
        return 0.0


def _get(url, params=None, timeout=30):
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            logger.warning("uasg_fetcher network error attempt=%d: %s", attempt, exc)
            time.sleep(_exp_backoff(attempt))
            continue

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 429:
            wait = max(_parse_retry_after(resp.headers.get("Retry-After")),
                       _exp_backoff(attempt))
            logger.warning("uasg_fetcher 429 backoff=%.1fs attempt=%d url=%s",
                           wait, attempt, url)
            time.sleep(wait)
            continue

        if 500 <= resp.status_code < 600:
            wait = _exp_backoff(attempt)
            logger.warning("uasg_fetcher %d backoff=%.1fs attempt=%d",
                           resp.status_code, wait, attempt)
            time.sleep(wait)
            continue

        resp.raise_for_status()

    if last_exc:
        raise last_exc
    raise RuntimeError(f"uasg_fetcher exhausted retries: {url}")


def _fetch_arps_page(uasg, data_inicio, data_fim, pagina=1):
    return _get(f"{API_BASE}/1_consultarARP", {
        'pagina': pagina,
        'tamanhoPagina': PAGE_SIZE,
        'codigoUnidadeGerenciadora': uasg,
        'dataVigenciaInicialMin': data_inicio,
        'dataVigenciaInicialMax': data_fim,
    })


def fetch_all_arps(uasg, data_inicio='2024-04-22'):
    start = datetime.strptime(data_inicio, '%Y-%m-%d')
    end = datetime.now()
    collected = []
    win_start = start
    while win_start < end:
        win_end = min(win_start + timedelta(days=365), end)
        di = win_start.strftime('%Y-%m-%d')
        df = win_end.strftime('%Y-%m-%d')
        try:
            first = _fetch_arps_page(uasg, di, df, 1)
        except Exception as e:
            logger.warning("fetch_arps window %s-%s failed: %s", di, df, e)
            win_start = win_end
            continue
        collected.extend(first.get('resultado') or [])
        total_pages = int(first.get('totalPaginas') or 1)
        for p in range(2, total_pages + 1):
            time.sleep(SLEEP)
            try:
                more = _fetch_arps_page(uasg, di, df, p)
                collected.extend(more.get('resultado') or [])
            except Exception as e:
                logger.warning("fetch_arps page %d failed: %s", p, e)
        win_start = win_end
        time.sleep(SLEEP)
    seen = set()
    unique = []
    for arp in collected:
        key = arp.get('numeroControlePncpAta')
        if key and key not in seen:
            seen.add(key)
            unique.append(arp)
    return unique


def fetch_arp_itens(numero_controle):
    try:
        result = _get(f"{API_BASE}/2.1_consultarARPItem_Id",
                      {'numeroControlePncpAta': numero_controle})
        return result.get('resultado') or []
    except Exception as e:
        logger.warning("fetch_itens %s failed: %s", numero_controle, e)
        return []


def fetch_arp_empenhos(numero_ata, uasg):
    try:
        result = _get(f"{API_BASE}/4_consultarEmpenhosSaldoItem", {
            'pagina': 1,
            'tamanhoPagina': PAGE_SIZE,
            'numeroAta': numero_ata,
            'unidadeGerenciadora': uasg,
        })
        return result.get('resultado') or []
    except Exception as e:
        logger.warning("fetch_empenhos %s failed: %s", numero_ata, e)
        return []
