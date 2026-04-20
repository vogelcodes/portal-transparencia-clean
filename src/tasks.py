from celery import Celery
import os
import io
import base64
import time
from datetime import datetime

from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TextProperties, TableCellProperties
from odf.text import P
from odf.table import Table, TableColumn, TableRow, TableCell

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
    from src.portal_api import get_empenhos_list, get_empenho_details, get_rate_limit_delay
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
                time.sleep(get_rate_limit_delay())
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
    from src.auth.models import Search, SearchResult

    with app.app_context():
        search = Search.query.get(search_id)
        if not search:
            raise ValueError(f"Search {search_id} not found")
        rows = (SearchResult.query
                .filter_by(search_id=search_id, included=True)
                .order_by(SearchResult.data.desc().nullslast())
                .all())
        pregao_filter = search.pregao_filter or ''

        detailed_empenhos = []
        for r in rows:
            base = dict(r.detail_json or {})
            base.setdefault('documento', r.documento)
            base.setdefault('documentoResumido', r.documento_resumido or r.documento)
            base.setdefault('data', r.data.strftime('%d/%m/%Y') if r.data else '')
            if 'valor' not in base:
                v = float(r.valor) if r.valor is not None else 0.0
                base['valor'] = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            base.setdefault('ug', r.ug or '')
            base.setdefault('codigoUg', r.codigo_ug or '')
            base.setdefault('orgao', r.orgao or '')
            base.setdefault('codigoOrgao', r.codigo_orgao or '')
            base.setdefault('numeroProcesso', r.numero_processo or '')
            base.setdefault('observacao', r.observacao or '')
            base.setdefault('categoria', r.categoria or '')
            base.setdefault('grupo', r.grupo or '')
            base.setdefault('elemento', r.elemento or '')
            detailed_empenhos.append(base)

    doc = OpenDocumentSpreadsheet()

    header_style = Style(name="HeaderCell", family="table-cell")
    header_style.addElement(TextProperties(fontweight="bold"))
    header_style.addElement(TableCellProperties(backgroundcolor="#2c3e50"))
    doc.automaticstyles.addElement(header_style)

    table = Table(name="Empenhos")
    columns = ["Data", "Documento", "Unidade Gestora", "Órgão", "Valor (R$)",
               "Número do Processo", "Descrição", "Categoria", "Grupo", "Elemento"]
    for _ in columns:
        table.addElement(TableColumn())

    header_row = TableRow()
    for col_name in columns:
        cell = TableCell(valuetype="string", stylename="HeaderCell")
        cell.addElement(P(text=col_name))
        header_row.addElement(cell)
    table.addElement(header_row)

    total = 0.0
    for emp in detailed_empenhos:
        row = TableRow()

        def add_cell(val, _row=row):
            c = TableCell(valuetype="string")
            c.addElement(P(text=str(val) if val is not None else ""))
            _row.addElement(c)

        add_cell(emp.get('data', ''))
        add_cell(emp.get('documentoResumido') or emp.get('documento', ''))
        add_cell(f"{emp.get('codigoUg', '')} - {emp.get('ug', '')}")
        add_cell(f"{emp.get('codigoOrgao', '')} - {emp.get('orgao', '')}")

        val_raw = emp.get('valor', '0')
        try:
            val_float = float(str(val_raw).replace('.', '').replace(',', '.'))
            total += val_float
            val_str = f"{val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            val_str = str(val_raw)
        add_cell(val_str)

        add_cell(emp.get('numeroProcesso', ''))
        add_cell(emp.get('observacao', ''))
        add_cell(emp.get('categoria', ''))
        add_cell(emp.get('grupo', ''))
        add_cell(emp.get('elemento', ''))

        table.addElement(row)

    blank_row = TableRow()
    for _ in columns:
        blank_row.addElement(TableCell())
    table.addElement(blank_row)

    total_row = TableRow()
    total_label = TableCell(valuetype="string")
    total_label.addElement(P(text="TOTAL"))
    total_row.addElement(total_label)
    for _ in range(3):
        total_row.addElement(TableCell())
    total_val_cell = TableCell(valuetype="string")
    total_fmt = f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    total_val_cell.addElement(P(text=total_fmt))
    total_row.addElement(total_val_cell)
    table.addElement(total_row)

    doc.spreadsheet.addElement(table)

    buf = io.BytesIO()
    doc.save(buf)
    filename = f"empenhos_{pregao_filter or 'todos'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ods"
    return {
        'ods_b64': base64.b64encode(buf.getvalue()).decode(),
        'filename': filename,
    }
