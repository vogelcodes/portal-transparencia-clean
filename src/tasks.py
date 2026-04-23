from celery import Celery
import os
import base64
from datetime import datetime, timezone

celery = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL")),
    backend=os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL")),
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
)


@celery.task(name="health_check")
def health_check():
    return {"status": "ok"}


@celery.task(name="fetch_enrichment", max_retries=3, default_retry_delay=30)
def fetch_enrichment(result_id):
    from src.app import app
    from src.portal_api import get_itens_empenho, get_item_historico, get_documentos_relacionados, get_empresa
    from src.auth.models import SearchResult
    from src.db import db

    with app.app_context():
        r = SearchResult.query.get(result_id)
        if not r:
            return {"status": "missing"}
        cnpj = r.search.cnpj
        itens = get_itens_empenho(r.documento)
        for item in itens:
            item['historico'] = get_item_historico(r.documento, item['sequencial'])
        r.enrichment_json = {
            "itens_empenho": itens,
            "documentos_relacionados": get_documentos_relacionados(r.documento),
            "empresa": get_empresa(cnpj),
        }
        r.enriched_at = datetime.now(timezone.utc)
        db.session.commit()
        return {"status": "done", "result_id": result_id}


def _parse_br_date(s):
    try:
        return datetime.strptime(s, '%d/%m/%Y').date()
    except Exception:
        return None


def _parse_br_money(s):
    try:
        if s is None:
            return None
        return float(str(s).replace('.', '').replace(',', '.'))
    except Exception:
        return None


@celery.task(name="fetch_search_results")
def fetch_search_results(search_id):
    from src.app import app
    from src.portal_api import get_empenhos_list, get_empenho_details, get_empresa
    from src.auth.models import Search, SearchResult
    from src.db import db

    with app.app_context():
        search = Search.query.get(search_id)
        if not search:
            return {"status": "missing"}
        search.status = 'fetching'
        db.session.commit()

        try:
            current_year = datetime.now().year
            years = sorted({2024, 2025, current_year}, reverse=True)

            seen = set()
            raws = []
            for y in years:
                for emp in get_empenhos_list(search.cnpj, y):
                    obs = emp.get('observacao', '') or ''
                    if search.pregao_filter and search.pregao_filter not in obs:
                        continue
                    doc = emp.get('documento')
                    if not doc or doc in seen:
                        continue
                    seen.add(doc)
                    raws.append(emp)

            for emp in raws:
                doc = emp['documento']
                existing = SearchResult.query.filter_by(
                    search_id=search.id, documento=doc
                ).first()
                if existing:
                    continue
                details = get_empenho_details(doc) or {}
                merged = {**emp, **{k: v for k, v in details.items() if v is not None}}
                sr = SearchResult(
                    search_id=search.id,
                    documento=doc,
                    documento_resumido=merged.get('documentoResumido'),
                    data=_parse_br_date(merged.get('data', '')),
                    valor=_parse_br_money(merged.get('valor')),
                    orgao=merged.get('orgao'),
                    codigo_orgao=str(merged.get('codigoOrgao') or '') or None,
                    ug=merged.get('ug'),
                    codigo_ug=str(merged.get('codigoUg') or '') or None,
                    numero_processo=merged.get('numeroProcesso'),
                    observacao=merged.get('observacao'),
                    categoria=merged.get('categoria'),
                    grupo=merged.get('grupo'),
                    elemento=merged.get('elemento'),
                    raw_json=emp,
                    detail_json=details,
                )
                db.session.add(sr)
                db.session.commit()
                fetch_enrichment.delay(sr.id)

            empresa = get_empresa(search.cnpj)
            search.name = empresa.get('razaoSocial') or search.cnpj
            search.status = 'done'
            db.session.commit()
            return {"status": "done", "count": len(raws)}
        except Exception as e:
            db.session.rollback()
            search.status = 'error'
            search.error = str(e)[:2000]
            db.session.commit()
            raise


def _parse_iso_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00')).date()
    except Exception:
        try:
            return datetime.strptime(str(s)[:10], '%Y-%m-%d').date()
        except Exception:
            return None


def _to_decimal(v):
    if v is None:
        return None
    try:
        if isinstance(v, str):
            return float(v.replace('.', '').replace(',', '.')) if ',' in v else float(v)
        return float(v)
    except Exception:
        return None


@celery.task(name="sync_uasg_data", max_retries=1, default_retry_delay=120)
def sync_uasg_data(user_uasg_id, full_refresh=False):
    from collections import defaultdict
    from src.app import app
    from src.auth.models import UserUasg, Arp, ArpItem, ArpEmpenho
    from src.uasg_fetcher import fetch_all_arps, fetch_arp_itens, fetch_arp_empenhos, SLEEP
    from src.db import db
    import time as _time

    with app.app_context():
        u = UserUasg.query.get(user_uasg_id)
        if not u:
            return {"status": "missing"}
        u.sync_status = 'syncing'
        u.sync_error = None
        u.last_arp_count = 0
        db.session.commit()

        if full_refresh:
            Arp.query.filter_by(user_uasg_id=u.id).delete(synchronize_session=False)
            db.session.commit()

        try:
            arps_data = fetch_all_arps(u.codigo_uasg, data_inicio='2024-04-22')

            for arp_data in arps_data:
                numero_controle = arp_data.get('numeroControlePncpAta') or ''
                if not numero_controle:
                    continue

                arp = Arp.query.filter_by(
                    user_uasg_id=u.id,
                    numero_controle_pncp_ata=numero_controle,
                ).first()
                if not arp:
                    arp = Arp(user_uasg_id=u.id, numero_controle_pncp_ata=numero_controle)
                    db.session.add(arp)

                arp.numero_ata_registro_preco = arp_data.get('numeroAtaRegistroPreco')
                arp.data_vigencia_inicial = _parse_iso_date(arp_data.get('dataVigenciaInicial'))
                arp.data_vigencia_final = _parse_iso_date(arp_data.get('dataVigenciaFinal'))
                arp.objeto = arp_data.get('objetoContratacao') or arp_data.get('objeto')
                arp.raw_json = arp_data
                db.session.flush()

                itens_data = fetch_arp_itens(numero_controle)
                _time.sleep(SLEEP)

                existing_items = {it.numero_item: it for it in arp.items}
                for item_data in itens_data:
                    num_item = str(item_data.get('numeroItem') or '')
                    if not num_item:
                        continue
                    item = existing_items.get(num_item)
                    if not item:
                        item = ArpItem(arp_id=arp.id, numero_item=num_item)
                        db.session.add(item)
                        existing_items[num_item] = item
                    item.descricao = item_data.get('descricaoItem') or item_data.get('descricao')
                    item.quantidade = _to_decimal(item_data.get('quantidadeRegistrada'))
                    item.valor_unitario = _to_decimal(item_data.get('valorUnitarioRegistrado'))
                    item.raw_json = item_data
                db.session.flush()

                numero_ata = arp_data.get('numeroAtaRegistroPreco')
                if numero_ata:
                    empenhos_data = fetch_arp_empenhos(numero_ata, u.codigo_uasg)
                    _time.sleep(SLEEP)

                    empenhos_by_item = defaultdict(list)
                    for emp in empenhos_data:
                        empenhos_by_item[str(emp.get('numeroItem') or '')].append(emp)

                    for item in arp.items:
                        for old in list(item.empenhos):
                            db.session.delete(old)
                        for emp_data in empenhos_by_item.get(item.numero_item, []):
                            emp = ArpEmpenho(
                                arp_item_id=item.id,
                                numero_empenho=str(emp_data.get('numeroEmpenho') or ''),
                                valor=_to_decimal(emp_data.get('valorEmpenho')),
                                data=_parse_iso_date(emp_data.get('dataEmissao')),
                                raw_json=emp_data,
                            )
                            db.session.add(emp)

                db.session.commit()

            u.sync_status = 'done'
            u.synced_at = datetime.now(timezone.utc)
            u.last_arp_count = len(arps_data)
            db.session.commit()
            return {"status": "done", "arps": len(arps_data)}

        except Exception as e:
            db.session.rollback()
            u2 = UserUasg.query.get(user_uasg_id)
            if u2:
                u2.sync_status = 'error'
                u2.sync_error = str(e)[:2000]
                db.session.commit()
            raise


@celery.task(name="export_uasg_xlsx")
def export_uasg_xlsx_task(user_uasg_id):
    from src.app import app
    from src.exports import flatten_uasg, render_arp_xlsx
    with app.app_context():
        bundle = flatten_uasg(user_uasg_id)
        blob = render_arp_xlsx(bundle)
    slug = bundle['meta']['codigo_uasg']
    filename = f"arp_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return {'blob_b64': base64.b64encode(blob).decode(), 'filename': filename,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}


@celery.task(name="export_uasg_csv")
def export_uasg_csv_task(user_uasg_id):
    from src.app import app
    from src.exports import flatten_uasg, render_arp_csv
    with app.app_context():
        bundle = flatten_uasg(user_uasg_id)
        blob = render_arp_csv(bundle)
    slug = bundle['meta']['codigo_uasg']
    filename = f"arp_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return {'blob_b64': base64.b64encode(blob).decode(), 'filename': filename,
            'mimetype': 'text/csv'}


@celery.task(name="export_uasg_ods")
def export_uasg_ods_task(user_uasg_id):
    from src.app import app
    from src.exports import flatten_uasg, render_arp_ods
    with app.app_context():
        bundle = flatten_uasg(user_uasg_id)
        blob = render_arp_ods(bundle)
    slug = bundle['meta']['codigo_uasg']
    filename = f"arp_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ods"
    return {'blob_b64': base64.b64encode(blob).decode(), 'filename': filename,
            'mimetype': 'application/vnd.oasis.opendocument.spreadsheet'}


@celery.task(name="generate_ods")
def generate_ods_task(search_id):
    from src.app import app
    from src.exports import flatten_search, render_ods

    with app.app_context():
        bundle = flatten_search(search_id)
        cnpj = bundle['meta']['cnpj']
        empresa = bundle.get('empresa') or {}
        nome = empresa.get('razaoSocial', '') or ''
        nome_slug = nome[:10].replace(' ', '_') if nome else 'empresa'
        blob = render_ods(bundle)

    filename = f"{cnpj}-{nome_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ods"
    return {
        'ods_b64': base64.b64encode(blob).decode(),
        'filename': filename,
    }


@celery.task(name="generate_xlsx")
def generate_xlsx_task(search_id):
    from src.app import app
    from src.exports import flatten_search, render_xlsx

    with app.app_context():
        bundle = flatten_search(search_id)
        cnpj = bundle['meta']['cnpj']
        empresa = bundle.get('empresa') or {}
        nome = empresa.get('razaoSocial', '') or ''
        nome_slug = nome[:10].replace(' ', '_') if nome else 'empresa'
        blob = render_xlsx(bundle)

    filename = f"{cnpj}-{nome_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return {
        'xlsx_b64': base64.b64encode(blob).decode(),
        'filename': filename,
    }


@celery.task(name="generate_csv")
def generate_csv_task(search_id):
    from src.app import app
    from src.exports import flatten_search, render_csv

    with app.app_context():
        bundle = flatten_search(search_id)
        cnpj = bundle['meta']['cnpj']
        empresa = bundle.get('empresa') or {}
        nome = empresa.get('razaoSocial', '') or ''
        nome_slug = nome[:10].replace(' ', '_') if nome else 'empresa'
        blob = render_csv(bundle)

    filename = f"{cnpj}-{nome_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return {
        'csv_b64': base64.b64encode(blob).decode(),
        'filename': filename,
    }
