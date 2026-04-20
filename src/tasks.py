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


@celery.task(name="generate_ods")
def generate_ods_task(selected_ids, pregao_filter):
    from src.portal_api import get_empenho_details, get_rate_limit_delay

    detailed_empenhos = []
    for doc_id in selected_ids:
        details = get_empenho_details(doc_id)
        if details:
            if 'documento' not in details:
                details['documento'] = doc_id
            detailed_empenhos.append(details)
        time.sleep(get_rate_limit_delay())

    detailed_empenhos.sort(
        key=lambda x: datetime.strptime(x.get('data', '01/01/2000'), '%d/%m/%Y'),
        reverse=True
    )

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
