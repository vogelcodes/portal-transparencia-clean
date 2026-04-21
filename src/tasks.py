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


@celery.task(name="generate_ods")
def generate_ods_task(search_id):
    from src.app import app
    from src.exports import flatten_search, render_ods

    with app.app_context():
        bundle = flatten_search(search_id)
        pregao = bundle['meta']['pregao_filter'] or 'todos'
        blob = render_ods(bundle)

    filename = f"empenhos_{pregao}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ods"
    return {
        'ods_b64': base64.b64encode(blob).decode(),
        'filename': filename,
    }
