"""
Portal da Transparência - SaaS
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_login import LoginManager
import time
import io
import base64
import os
from datetime import datetime

from src.tasks import celery, generate_ods_task
from src.db import db
from src.auth import auth_bp
from src.auth.models import User
from src.auth.decorators import require_auth
from src.portal_api import (
    get_empenhos_list, get_empenho_details,
    format_currency, format_date, get_rate_limit_delay
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', '')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()


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
@require_auth
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
@require_auth
def search():
    cnpj = request.form.get('cnpj')
    pregao = request.form.get('pregao')

    current_year = datetime.now().year
    years = sorted(list(set([2024, 2025, current_year])), reverse=True)

    empenhos = []
    for y in years:
        empenhos.extend(get_empenhos_list(cnpj, y))

    filtered = []
    for emp in empenhos:
        obs = emp.get('observacao', '')
        if not pregao or pregao in obs:
            emp['valor_fmt'] = format_currency(emp.get('valor', 0))
            filtered.append(emp)

    filtered.sort(
        key=lambda x: datetime.strptime(x.get('data', '01/01/2000'), '%d/%m/%Y'),
        reverse=True
    )

    return render_template('list.html', empenhos=filtered, cnpj=cnpj, pregao=pregao)


@app.route('/generate', methods=['POST'])
@require_auth
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
            except Exception:
                pass
            detailed_empenhos.append(details)
        time.sleep(get_rate_limit_delay())

    detailed_empenhos.sort(
        key=lambda x: datetime.strptime(x.get('data', '01/01/2000'), '%d/%m/%Y'),
        reverse=True
    )

    return render_template(
        'report.html',
        empenhos=detailed_empenhos,
        total_value=format_currency(total_value),
        count=len(detailed_empenhos),
        now=datetime.now().strftime('%d/%m/%Y às %H:%M'),
        pregao_filter=pregao_filter,
        format_currency=format_currency,
        format_date=format_date,
        str=str
    )


@app.route('/export/ods', methods=['POST'])
@require_auth
def export_ods():
    selected_ids = request.form.getlist('selected_ids')
    pregao_filter = request.form.get('pregao_filter', '')
    task = generate_ods_task.delay(selected_ids, pregao_filter)
    return redirect(url_for('export_ods_wait', task_id=task.id))


@app.route('/export/ods/wait/<task_id>')
@require_auth
def export_ods_wait(task_id):
    return render_template('export_wait.html', task_id=task_id)


@app.route('/export/ods/status/<task_id>')
@require_auth
def export_ods_status(task_id):
    result = generate_ods_task.AsyncResult(task_id)
    if result.state == 'SUCCESS':
        return jsonify({'status': 'SUCCESS'})
    if result.state == 'FAILURE':
        return jsonify({'status': 'FAILURE', 'error': str(result.info)})
    return jsonify({'status': result.state})


@app.route('/export/ods/download/<task_id>')
@require_auth
def export_ods_download(task_id):
    result = generate_ods_task.AsyncResult(task_id)
    if result.state != 'SUCCESS':
        return redirect(url_for('export_ods_wait', task_id=task_id))
    data = result.get()
    buf = io.BytesIO(base64.b64decode(data['ods_b64']))
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/vnd.oasis.opendocument.spreadsheet',
        as_attachment=True,
        download_name=data['filename']
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
