"""Render export bundle to CSV."""
import csv
import io

from src.exports.parse import fmt_br_money


def _fmt_val(v):
    if v is None:
        return ''
    return str(v)


def _fmt_num(v):
    if v is None or v == '':
        return ''
    try:
        return fmt_br_money(float(v))
    except Exception:
        return _fmt_val(v)


def _fmt_bool(v):
    if v is None or v == '':
        return ''
    return 'Sim' if v else 'Não'


def _escape(val):
    """Escape value for CSV - wrap in quotes if contains comma, newline, or quotes."""
    s = str(val if val is not None else '')
    if ',' in s or '\n' in s or '"' in s:
        return '"' + s.replace('"', '""') + '"'
    return s


def render_csv(bundle):
    """Render ExportBundle dict to CSV bytes (empennho rows only)."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator='\n')
    
    # Header row
    cols = [
        'Data', 'Documento', 'Resumido', 'Valor (R$)', 'Fase', 'Espécie',
        'Favorecido', 'Cód. Favorecido', 'Nome Favorecido', 'UF Favorecido',
        'Cód. UG', 'UG', 'Cód. UO', 'UO', 'Cód. Órgão', 'Órgão',
        'Cód. Órgão Superior', 'Órgão Superior', 'Função', 'Subfunção',
        'Programa', 'Ação', 'Subtítulo', 'Localizador Gasto',
        'Categoria', 'Grupo', 'Elemento', 'Modalidade',
        'Nº Processo', 'Plano Orçamentário', 'Observação', 'Autor',
        'Favorecido Intermediário', 'Enriquecido'
    ]
    writer.writerow(cols)
    
    # Data rows
    for e in bundle.get('empenhos', []):
        row = [
            _escape(e.get('data', '')),
            _escape(e.get('documento', '')),
            _escape(e.get('documentoResumido', '')),
            _fmt_num(e.get('valor', '')),
            _escape(e.get('fase', '')),
            _escape(e.get('especie', '')),
            _escape(e.get('favorecido', '')),
            _escape(e.get('codigoFavorecido', '')),
            _escape(e.get('nomeFavorecido', '')),
            _escape(e.get('ufFavorecido', '')),
            _escape(e.get('codigoUg', '')),
            _escape(e.get('ug', '')),
            _escape(e.get('codigoUo', '')),
            _escape(e.get('uo', '')),
            _escape(e.get('codigoOrgao', '')),
            _escape(e.get('orgao', '')),
            _escape(e.get('codigoOrgaoSuperior', '')),
            _escape(e.get('orgaoSuperior', '')),
            _escape(e.get('funcao', '')),
            _escape(e.get('subfuncao', '')),
            _escape(e.get('programa', '')),
            _escape(e.get('acao', '')),
            _escape(e.get('subTitulo', '')),
            _escape(e.get('localizadorGasto', '')),
            _escape(e.get('categoria', '')),
            _escape(e.get('grupo', '')),
            _escape(e.get('elemento', '')),
            _escape(e.get('modalidade', '')),
            _escape(e.get('numeroProcesso', '')),
            _escape(e.get('planoOrcamentario', '')),
            _escape(e.get('observacao', '')),
            _escape(e.get('autor', '')),
            _escape(e.get('favorecidoIntermediario', '')),
            _fmt_bool(e.get('enriched', '')),
        ]
        writer.writerow(row)
    
    return buf.getvalue().encode('utf-8')