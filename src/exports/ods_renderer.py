import io
import zipfile
import re

from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TextProperties, TableCellProperties
from odf.text import P, A
from odf.table import Table, TableColumn, TableRow, TableCell

from src.exports.parse import fmt_br_money


def _set_column_widths(ods_bytes):
    """Post-process ODS XML to set column widths based on content."""
    # ODS is a ZIP file; extract, modify content.xml, repack
    buf_in = io.BytesIO(ods_bytes)
    buf_out = io.BytesIO()
    
    with zipfile.ZipFile(buf_in, 'r') as zin:
        with zipfile.ZipFile(buf_out, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == 'content.xml':
                    data = _fix_column_widths(data)
                zout.writestr(item, data)
    
    return buf_out.getvalue()


def _fix_column_widths(xml_bytes):
    """Parse XML, calculate column widths, add style:column-width attributes."""
    content = xml_bytes.decode('utf-8')
    
    def process_table(match):
        table_xml = match.group(0)
        
        # Count columns
        col_pattern = re.compile(r'<table:table-column[^>]*/>')
        cols = list(col_pattern.finditer(table_xml))
        num_cols = len(cols)
        
        if num_cols == 0:
            return table_xml
        
        # Track max text length per column
        col_widths = [0] * num_cols
        
        cell_pattern = re.compile(r'<table:table-cell[^>]*>(.*?)</table:table-cell>', re.DOTALL)
        row_pattern = re.compile(r'<table:table-row[^>]*>(.*?)</table:table-row>', re.DOTALL)
        
        # First: header row
        rows = list(row_pattern.finditer(table_xml))
        if rows:
            cells = list(cell_pattern.finditer(rows[0].group(1)))
            for i, cell_match in enumerate(cells):
                if i < num_cols:
                    clean = re.sub(r'<[^>]+>', '', cell_match.group(1)).strip()
                    col_widths[i] = max(col_widths[i], len(clean))
        
        # Second: all other rows
        for row in rows[1:]:
            cells = list(cell_pattern.finditer(row.group(1)))
            for i, cell_match in enumerate(cells):
                if i < num_cols:
                    clean = re.sub(r'<[^>]+>', '', cell_match.group(1)).strip()
                    if len(clean) > col_widths[i]:
                        col_widths[i] = len(clean)
        
        # Character to cm: min 1.5cm, max 12cm
        widths_cm = [max(1.5, min(12.0, w * 0.35 + 1.0)) for w in col_widths]
        
        # Replace each <table:table-column...> with style:column-width
        # We'll use a counter instead of regex groups
        col_idx = [0]  # closure-safe counter
        
        def replace_col(m):
            idx = col_idx[0]
            col_idx[0] += 1
            if idx < len(widths_cm):
                return f'<table:table-column style:column-width="{widths_cm[idx]:.1f}cm"/>'
            return m.group(0)
        
        new_table = col_pattern.sub(replace_col, table_xml)
        return new_table
    
    content = re.sub(r'<table:table[^>]*>.*?</table:table>', process_table, content, flags=re.DOTALL)
    
    return content.encode('utf-8')


def _style_header(doc):
    s = Style(name="HeaderCell", family="table-cell")
    s.addElement(TextProperties(fontweight="bold", color="#ffffff"))
    s.addElement(TableCellProperties(backgroundcolor="#2c3e50"))
    doc.automaticstyles.addElement(s)
    return s


def _style_title(doc):
    s = Style(name="TitleCell", family="table-cell")
    s.addElement(TextProperties(fontweight="bold", fontsize="14pt"))
    doc.automaticstyles.addElement(s)
    return s


def _style_label(doc):
    s = Style(name="LabelCell", family="table-cell")
    s.addElement(TextProperties(fontweight="bold"))
    doc.automaticstyles.addElement(s)
    return s


def _text_cell(val, stylename=None):
    kw = {'valuetype': 'string'}
    if stylename:
        kw['stylename'] = stylename
    c = TableCell(**kw)
    c.addElement(P(text='' if val is None else str(val)))
    return c


def _num_cell(val):
    if val is None or val == '':
        return _text_cell('')
    try:
        f = float(val)
    except Exception:
        return _text_cell(val)
    c = TableCell(valuetype='float', value=f)
    c.addElement(P(text=fmt_br_money(f)))
    return c


def _bool_cell(val):
    if val is None or val == '':
        return _text_cell('')
    return _text_cell('Sim' if val else 'Não')


def _link_cell(url):
    c = TableCell(valuetype='string')
    if url:
        p = P()
        a = A(href=url, type="simple")
        a.addText(url)
        p.addElement(a)
        c.addElement(p)
    else:
        c.addElement(P(text=''))
    return c


def _add_table(doc, name, columns, header_style):
    table = Table(name=name)
    for _ in columns:
        table.addElement(TableColumn())
    header_row = TableRow()
    for col in columns:
        header_row.addElement(_text_cell(col, stylename=header_style))
    table.addElement(header_row)
    doc.spreadsheet.addElement(table)
    return table


def _sheet_resumo(doc, meta, empresa, title_style, label_style):
    table = Table(name="Resumo")
    for _ in range(2):
        table.addElement(TableColumn())

    def kv(row_table, k, v):
        row = TableRow()
        row.addElement(_text_cell(k, stylename=label_style))
        row.addElement(_text_cell(v))
        row_table.addElement(row)

    # Título
    trow = TableRow()
    trow.addElement(_text_cell("Relatório de Empenhos", stylename=title_style))
    trow.addElement(_text_cell(""))
    table.addElement(trow)
    table.addElement(TableRow())

    kv(table, "Razão/Nome", meta.get('search_name', ''))
    kv(table, "CNPJ", meta.get('cnpj', ''))
    kv(table, "Filtro Pregão", meta.get('pregao_filter', '') or '(todos)')
    kv(table, "Status da busca", meta.get('status', ''))
    kv(table, "Gerado em", meta.get('generated_at', ''))
    kv(table, "Empenhos", meta.get('count', 0))
    kv(table, "Enriquecidos", meta.get('enriched_count', 0))

    row = TableRow()
    row.addElement(_text_cell("Valor total (R$)", stylename=label_style))
    row.addElement(_num_cell(meta.get('total_valor', 0)))
    table.addElement(row)

    if empresa:
        table.addElement(TableRow())
        hrow = TableRow()
        hrow.addElement(_text_cell("Sanções / Cadastros", stylename=title_style))
        hrow.addElement(_text_cell(""))
        table.addElement(hrow)
        for k, label in [
            ('sancionadoCEIS', 'Inidôneos (CEIS)'),
            ('sancionadoCNEP', 'Penalidades (CNEP)'),
            ('sancionadoCEPIM', 'Entidades Privadas (CEPIM)'),
            ('sancionadoCEAF', 'CEAF'),
            ('favorecidoDespesas', 'Favorecido Despesas'),
            ('possuiContratacao', 'Possui Contratação'),
            ('convenios', 'Convênios'),
            ('favorecidoTransferencias', 'Favorecido Transferências'),
            ('participanteLicitacao', 'Participante Licitação'),
            ('emitiuNFe', 'Emitiu NFe'),
            ('beneficiadoRenunciaFiscal', 'Beneficiado Renúncia Fiscal'),
            ('isentoImuneRenunciaFiscal', 'Isento/Imune Renúncia Fiscal'),
            ('habilitadoRenunciaFiscal', 'Habilitado Renúncia Fiscal'),
        ]:
            r = TableRow()
            r.addElement(_text_cell(label, stylename=label_style))
            r.addElement(_bool_cell(empresa.get(k)))
            table.addElement(r)

    doc.spreadsheet.addElement(table)


def _sheet_empenhos(doc, empenhos, header_style):
    cols = [
        ('Data', 'data', 'str'),
        ('Documento', 'documento', 'str'),
        ('Resumido', 'documentoResumido', 'str'),
        ('Valor (R$)', 'valor', 'num'),
        ('Fase', 'fase', 'str'),
        ('Espécie', 'especie', 'str'),
        ('Favorecido', 'favorecido', 'str'),
        ('Cód. Favorecido', 'codigoFavorecido', 'str'),
        ('Nome Favorecido', 'nomeFavorecido', 'str'),
        ('UF Favorecido', 'ufFavorecido', 'str'),
        ('Cód. UG', 'codigoUg', 'str'),
        ('UG', 'ug', 'str'),
        ('Cód. UO', 'codigoUo', 'str'),
        ('UO', 'uo', 'str'),
        ('Cód. Órgão', 'codigoOrgao', 'str'),
        ('Órgão', 'orgao', 'str'),
        ('Cód. Órgão Superior', 'codigoOrgaoSuperior', 'str'),
        ('Órgão Superior', 'orgaoSuperior', 'str'),
        ('Função', 'funcao', 'str'),
        ('Subfunção', 'subfuncao', 'str'),
        ('Programa', 'programa', 'str'),
        ('Ação', 'acao', 'str'),
        ('Subtítulo', 'subTitulo', 'str'),
        ('Localizador Gasto', 'localizadorGasto', 'str'),
        ('Categoria', 'categoria', 'str'),
        ('Grupo', 'grupo', 'str'),
        ('Elemento', 'elemento', 'str'),
        ('Modalidade', 'modalidade', 'str'),
        ('Nº Processo', 'numeroProcesso', 'str'),
        ('Plano Orçamentário', 'planoOrcamentario', 'str'),
        ('Observação', 'observacao', 'str'),
        ('Autor', 'autor', 'str'),
        ('Favorecido Intermediário', 'favorecidoIntermediario', 'str'),
        ('Enriquecido', 'enriched', 'bool'),
    ]
    table = _add_table(doc, "Empenhos", [c[0] for c in cols], header_style)
    for e in empenhos:
        row = TableRow()
        for _, key, kind in cols:
            v = e.get(key, '')
            if kind == 'num':
                row.addElement(_num_cell(v))
            elif kind == 'bool':
                row.addElement(_bool_cell(v))
            else:
                row.addElement(_text_cell(v))
        table.addElement(row)


def _sheet_itens(doc, itens, header_style):
    cols = [
        ('Documento', 'documento', 'str'),
        ('Sequencial', 'sequencial', 'str'),
        ('Cód. Item', 'codigoItemEmpenho', 'str'),
        ('Descrição', 'descricao', 'str'),
        ('Cód. Subelemento', 'codigoSubelemento', 'str'),
        ('Subelemento', 'descricaoSubelemento', 'str'),
        ('Valor Atual (R$)', 'valorAtual_num', 'num'),
    ]
    table = _add_table(doc, "Itens", [c[0] for c in cols], header_style)
    for it in itens:
        row = TableRow()
        for _, key, kind in cols:
            v = it.get(key, '')
            if kind == 'num':
                row.addElement(_num_cell(v))
            else:
                row.addElement(_text_cell(v))
        table.addElement(row)


def _sheet_historico(doc, historico, header_style):
    cols = [
        ('Documento', 'documento', 'str'),
        ('Sequencial', 'sequencial', 'str'),
        ('Data', 'data', 'str'),
        ('Operação', 'operacao', 'str'),
        ('Quantidade', 'quantidade_num', 'num'),
        ('Valor Unitário (R$)', 'valorUnitario_num', 'num'),
        ('Valor Total (R$)', 'valorTotal_num', 'num'),
    ]
    table = _add_table(doc, "Historico", [c[0] for c in cols], header_style)
    for h in historico:
        row = TableRow()
        for _, key, kind in cols:
            v = h.get(key, '')
            if kind == 'num':
                row.addElement(_num_cell(v))
            else:
                row.addElement(_text_cell(v))
        table.addElement(row)


def _sheet_relacionados(doc, relacionados, header_style):
    cols = [
        ('Empenho Origem', 'documento_empenho', 'str'),
        ('Data', 'data', 'str'),
        ('Fase', 'fase', 'str'),
        ('Documento', 'documento', 'str'),
        ('Resumido', 'documentoResumido', 'str'),
        ('Espécie', 'especie', 'str'),
        ('Órgão Superior', 'orgaoSuperior', 'str'),
        ('Órgão Vinculado', 'orgaoVinculado', 'str'),
        ('Unidade Gestora', 'unidadeGestora', 'str'),
        ('Elemento Despesa', 'elementoDespesa', 'str'),
        ('Favorecido', 'favorecido', 'str'),
        ('Valor (R$)', 'valor_num', 'num'),
        ('Link Portal', 'url_portal', 'link'),
    ]
    table = _add_table(doc, "Documentos Relacionados", [c[0] for c in cols], header_style)
    for rel in relacionados:
        row = TableRow()
        for _, key, kind in cols:
            v = rel.get(key, '')
            if kind == 'num':
                row.addElement(_num_cell(v))
            elif kind == 'link':
                row.addElement(_link_cell(v))
            else:
                row.addElement(_text_cell(v))
        table.addElement(row)


def _sheet_empresa(doc, empresa, header_style, label_style):
    if not empresa:
        return
    table = Table(name="Empresa")
    table.addElement(TableColumn())
    table.addElement(TableColumn())

    for key, label in [
        ('cnpj', 'CNPJ'),
        ('razaoSocial', 'Razão Social'),
        ('nomeFantasia', 'Nome Fantasia'),
        ('favorecidoDespesas', 'Favorecido Despesas'),
        ('possuiContratacao', 'Possui Contratação'),
        ('convenios', 'Convênios'),
        ('favorecidoTransferencias', 'Favorecido Transferências'),
        ('sancionadoCEIS', 'Sancionado CEIS (Inidôneos)'),
        ('sancionadoCNEP', 'Sancionado CNEP (Penalidades)'),
        ('sancionadoCEPIM', 'Sancionado CEPIM (Entidades Privadas)'),
        ('sancionadoCEAF', 'Sancionado CEAF'),
        ('participanteLicitacao', 'Participante Licitação'),
        ('emitiuNFe', 'Emitiu NFe'),
        ('beneficiadoRenunciaFiscal', 'Beneficiado Renúncia Fiscal'),
        ('isentoImuneRenunciaFiscal', 'Isento/Imune Renúncia Fiscal'),
        ('habilitadoRenunciaFiscal', 'Habilitado Renúncia Fiscal'),
    ]:
        row = TableRow()
        row.addElement(_text_cell(label, stylename=label_style))
        v = empresa.get(key)
        if isinstance(v, bool):
            row.addElement(_bool_cell(v))
        else:
            row.addElement(_text_cell(v))
        table.addElement(row)

    doc.spreadsheet.addElement(table)


def render_ods(bundle):
    """Render ExportBundle dict to .ods bytes with auto-width columns."""
    doc = OpenDocumentSpreadsheet()
    header_style = _style_header(doc)
    title_style = _style_title(doc)
    label_style = _style_label(doc)

    _sheet_resumo(doc, bundle['meta'], bundle.get('empresa') or {}, title_style, label_style)
    _sheet_empenhos(doc, bundle['empenhos'], header_style)
    _sheet_itens(doc, bundle['itens'], header_style)
    _sheet_historico(doc, bundle['historico'], header_style)
    _sheet_relacionados(doc, bundle['relacionados'], header_style)
    _sheet_empresa(doc, bundle.get('empresa') or {}, header_style, label_style)

    buf = io.BytesIO()
    doc.save(buf)
    ods_bytes = buf.getvalue()
    
    # Post-process XML to set column widths based on content
    return _set_column_widths(ods_bytes)
