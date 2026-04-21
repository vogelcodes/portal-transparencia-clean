from datetime import datetime, timezone

from src.auth.models import Search, SearchResult
from src.exports.parse import parse_br_money, fmt_br_date, portal_doc_url


EMPENHO_FIELDS = [
    'documento', 'documentoResumido', 'data', 'valor',
    'fase', 'especie',
    'favorecido', 'codigoFavorecido', 'nomeFavorecido', 'ufFavorecido',
    'codigoUg', 'ug', 'codigoUo', 'uo',
    'codigoOrgao', 'orgao', 'codigoOrgaoSuperior', 'orgaoSuperior',
    'funcao', 'subfuncao', 'programa', 'acao', 'subTitulo', 'localizadorGasto',
    'categoria', 'grupo', 'elemento', 'modalidade',
    'numeroProcesso', 'planoOrcamentario', 'observacao',
    'autor', 'favorecidoIntermediario', 'favorecidoListaFaturas',
]

ITEM_FIELDS = [
    'sequencial', 'codigoItemEmpenho', 'descricao',
    'codigoSubelemento', 'descricaoSubelemento', 'valorAtual',
]

HIST_FIELDS = [
    'data', 'operacao', 'quantidade', 'valorUnitario', 'valorTotal',
]

REL_FIELDS = [
    'data', 'fase', 'documento', 'documentoResumido', 'especie',
    'orgaoSuperior', 'orgaoVinculado', 'unidadeGestora',
    'elementoDespesa', 'favorecido', 'valor',
]

EMPRESA_FIELDS = [
    'cnpj', 'razaoSocial', 'nomeFantasia',
    'favorecidoDespesas', 'possuiContratacao', 'convenios',
    'favorecidoTransferencias',
    'sancionadoCEIS', 'sancionadoCNEP', 'sancionadoCEPIM', 'sancionadoCEAF',
    'participanteLicitacao', 'emitiuNFe',
    'beneficiadoRenunciaFiscal', 'isentoImuneRenunciaFiscal',
    'habilitadoRenunciaFiscal',
]


def _empenho_row(r):
    detail = dict(r.detail_json or {})
    row = {f: detail.get(f, '') for f in EMPENHO_FIELDS}
    row['documento'] = r.documento
    row['documentoResumido'] = r.documento_resumido or detail.get('documentoResumido', '')
    row['data'] = fmt_br_date(r.data) or detail.get('data', '')
    if r.valor is not None:
        row['valor'] = float(r.valor)
    else:
        row['valor'] = parse_br_money(detail.get('valor'))
    row['ug'] = r.ug or detail.get('ug', '')
    row['codigoUg'] = r.codigo_ug or str(detail.get('codigoUg') or '')
    row['orgao'] = r.orgao or detail.get('orgao', '')
    row['codigoOrgao'] = r.codigo_orgao or str(detail.get('codigoOrgao') or '')
    row['numeroProcesso'] = r.numero_processo or detail.get('numeroProcesso', '')
    row['observacao'] = r.observacao or detail.get('observacao', '')
    row['categoria'] = r.categoria or detail.get('categoria', '')
    row['grupo'] = r.grupo or detail.get('grupo', '')
    row['elemento'] = r.elemento or detail.get('elemento', '')
    row['enriched'] = r.enriched_at is not None
    return row


def _items_rows(r):
    enr = r.enrichment_json or {}
    out_items = []
    out_hist = []
    for item in enr.get('itens_empenho') or []:
        row = {f: item.get(f, '') for f in ITEM_FIELDS}
        row['documento'] = r.documento
        row['valorAtual_num'] = parse_br_money(item.get('valorAtual'))
        out_items.append(row)
        for h in item.get('historico') or []:
            hrow = {f: h.get(f, '') for f in HIST_FIELDS}
            hrow['documento'] = r.documento
            hrow['sequencial'] = item.get('sequencial', '')
            hrow['quantidade_num'] = parse_br_money(h.get('quantidade'))
            hrow['valorUnitario_num'] = parse_br_money(h.get('valorUnitario'))
            hrow['valorTotal_num'] = parse_br_money(h.get('valorTotal'))
            out_hist.append(hrow)
    return out_items, out_hist


def _relacionados_rows(r):
    enr = r.enrichment_json or {}
    out = []
    for rel in enr.get('documentos_relacionados') or []:
        row = {f: rel.get(f, '') for f in REL_FIELDS}
        row['documento_empenho'] = r.documento
        row['valor_num'] = parse_br_money(rel.get('valor'))
        row['url_portal'] = portal_doc_url(rel.get('fase'), rel.get('documento'))
        out.append(row)
    return out


def _empresa_row(results):
    """First non-empty empresa dict across results."""
    for r in results:
        enr = r.enrichment_json or {}
        emp = enr.get('empresa')
        if emp:
            return {f: emp.get(f, '') for f in EMPRESA_FIELDS}
    return {}


def flatten_search(search_id):
    search = Search.query.get(search_id)
    if not search:
        raise ValueError(f"Search {search_id} not found")
    rows = (SearchResult.query
            .filter_by(search_id=search_id, included=True)
            .order_by(SearchResult.data.desc().nullslast())
            .all())

    empenhos = []
    itens = []
    historico = []
    relacionados = []
    total = 0.0
    for r in rows:
        e = _empenho_row(r)
        empenhos.append(e)
        if isinstance(e.get('valor'), (int, float)):
            total += e['valor']
        i, h = _items_rows(r)
        itens.extend(i)
        historico.extend(h)
        relacionados.extend(_relacionados_rows(r))

    return {
        'meta': {
            'search_name': search.name or search.cnpj,
            'cnpj': search.cnpj,
            'pregao_filter': search.pregao_filter or '',
            'status': search.status,
            'generated_at': datetime.now(timezone.utc).astimezone().strftime('%d/%m/%Y %H:%M:%S'),
            'count': len(empenhos),
            'enriched_count': sum(1 for e in empenhos if e['enriched']),
            'total_valor': total,
        },
        'empresa': _empresa_row(rows),
        'empenhos': empenhos,
        'itens': itens,
        'historico': historico,
        'relacionados': relacionados,
    }
