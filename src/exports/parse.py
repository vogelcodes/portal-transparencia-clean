from datetime import datetime
import unicodedata


def parse_br_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%d/%m/%Y').date()
    except Exception:
        return None


def parse_br_money(s):
    if s is None or s == '':
        return None
    try:
        return float(str(s).replace('.', '').replace(',', '.'))
    except Exception:
        return None


def fmt_br_money(v):
    if v is None:
        return ''
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


def fmt_br_date(d):
    if d is None:
        return ''
    if isinstance(d, str):
        return d
    try:
        return d.strftime('%d/%m/%Y')
    except Exception:
        return str(d)


def _slug(s):
    if not s:
        return ''
    n = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return n.strip().lower()


def portal_doc_url(fase, documento):
    """Build portaldatransparencia.gov.br URL for a related document."""
    if not documento:
        return ''
    slug = _slug(fase)
    mapping = {
        'liquidacao': 'liquidacao',
        'pagamento': 'pagamento',
        'empenho': 'empenho',
    }
    path = mapping.get(slug)
    if not path:
        return ''
    return f"https://portaldatransparencia.gov.br/despesas/{path}/{documento}"
