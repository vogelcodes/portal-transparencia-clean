"""
Portal da Transparência - SaaS
"""
from flask import Flask, render_template, request, jsonify
import requests
import time
from datetime import datetime
from src.tasks import celery
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', '')

API_KEY = os.getenv("API_KEY_PORTAL")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "chave-api-dados": API_KEY
}


# === Rate Limiting Configuration ===
# API Limits: 400 req/min during the day, 700 req/min between 00:00-06:00 (local time)
LIMIT_DAY = 400
LIMIT_NIGHT = 700
NIGHT_START = 0   # 00:00
NIGHT_END = 6     # 06:00


def get_rate_limit_delay():
    """Returns delay in seconds between API requests based on time of day."""
    now = datetime.now()
    hour = now.hour
    
    if NIGHT_START <= hour < NIGHT_END:
        # Night time: 700 req/min (~0.086s between requests + 10% buffer)
        delay = (60.0 / LIMIT_NIGHT) * 1.1
    else:
        # Day time: 400 req/min (~0.165s between requests + 10% buffer)
        delay = (60.0 / LIMIT_DAY) * 1.1
    
    return delay


# Helpers
def format_currency(value):
    try:
        if isinstance(value, str):
            value = float(value.replace('.', '').replace(',', '.'))
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"R$ {value}"


def format_date(date_str):
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').strftime('%d/%m/%Y')
    except:
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
    retries = 0
    while True:
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                if retries < 3:
                    retries += 1
                    time.sleep(1)
                    continue
                else:
                    break
            data = r.json()
            if not data:
                break
            all_data.extend(data)
            params['pagina'] += 1
            retries = 0
            if len(data) < 15:
                break
            time.sleep(get_rate_limit_delay())
        except:
            if retries < 3:
                retries += 1
                time.sleep(1)
                continue
            else:
                break
    return all_data


def get_empenho_details(doc_id):
    url = f"https://api.portaldatransparencia.gov.br/api-de-dados/despesas/documentos/{doc_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        # Rate limiting after request
        time.sleep(get_rate_limit_delay())
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}


# === API Routes ===

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/info')
def info():
    return jsonify({
        'env': os.getenv('APP_ENV'),
        'domain': os.getenv('SERVICE_FQDN_WEB'),
        'db_configured': bool(os.getenv('DATABASE_URL'))
    })

# === App UI Routes ===

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    cnpj = request.form.get('cnpj')
    pregao = request.form.get('pregao')

    current_year = datetime.now().year
    years = [2024, 2025, current_year]
    years = sorted(list(set(years)), reverse=True)

    empenhos = []
    for y in years:
        empenhos.extend(get_empenhos_list(cnpj, y))

    filtered = []
    for emp in empenhos:
        obs = emp.get('observacao', '')
        if not pregao or (pregao and pregao in obs):
            emp['valor_fmt'] = format_currency(emp.get('valor', 0))
            filtered.append(emp)

    filtered.sort(key=lambda x: datetime.strptime(x.get('data', '01/01/2000'), '%d/%m/%Y'), reverse=True)

    return render_template('list.html', empenhos=filtered, cnpj=cnpj, pregao=pregao)

@app.route('/generate', methods=['POST'])
def generate():
    selected_ids = request.form.getlist('selected_ids')
    detailed_empenhos = []
    total_value = 0
    pregao_filter = request.form.get('pregao_filter', '')

    for doc_id in selected_ids:
        details = get_empenho_details(doc_id)
        if details:
            if 'documento' not in details:
                details['documento'] = doc_id
            try:
                val_str = details.get('valor', '0').replace('.', '').replace(',', '.')
                total_value += float(val_str)
            except:
                pass
            detailed_empenhos.append(details)
        time.sleep(get_rate_limit_delay())

    detailed_empenhos.sort(key=lambda x: datetime.strptime(x.get('data', '01/01/2000'), '%d/%m/%Y'), reverse=True)

    html = render_template('report.html',
                           empenhos=detailed_empenhos,
                           total_value=format_currency(total_value),
                           count=len(detailed_empenhos),
                           now=datetime.now().strftime('%d/%m/%Y às %H:%M'),
                           pregao_filter=pregao_filter,
                           format_currency=format_currency,
                           format_date=format_date,
                           str=str)

    return html


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
