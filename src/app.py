"""
Portal da Transparência - SaaS
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, abort
from flask_login import LoginManager, current_user
import io
import base64
import os

from src.tasks import generate_ods_task, generate_xlsx_task, generate_csv_task, fetch_search_results, fetch_enrichment
from src.db import db
from src.auth import auth_bp
from src.auth.models import User, Search, SearchResult
from src.auth.decorators import require_auth

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


@app.cli.command('init-db')
def init_db_command():
    """Create all tables."""
    db.create_all()
    print("DB initialized.")


# === Health ===

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


# === UI ===

@app.route('/', methods=['GET'])
@require_auth
def index():
    return render_template('index.html')


# === Searches ===

def _owned_search_or_404(search_id):
    s = Search.query.get_or_404(search_id)
    if s.user_id != current_user.id:
        abort(404)
    return s


@app.route('/searches', methods=['GET'])
@require_auth
def searches_list():
    items = (Search.query
             .filter_by(user_id=current_user.id)
             .order_by(Search.created_at.desc())
             .all())
    return render_template('searches.html', searches=items)


@app.route('/searches', methods=['POST'])
@require_auth
def searches_create():
    cnpj = (request.form.get('cnpj') or '').strip()
    pregao = (request.form.get('pregao') or '').strip()
    if not cnpj:
        return "CNPJ obrigatório", 400
    s = Search(
        user_id=current_user.id,
        name=None,
        cnpj=cnpj,
        pregao_filter=pregao or None,
        status='pending',
    )
    db.session.add(s)
    db.session.commit()
    fetch_search_results.delay(s.id)
    return redirect(url_for('searches_detail', search_id=s.id))


@app.route('/searches/<int:search_id>', methods=['GET', 'POST', 'DELETE'])
@require_auth
def searches_detail(search_id):
    s = _owned_search_or_404(search_id)
    is_delete = request.method == 'DELETE' or (
        request.method == 'POST' and request.form.get('_method') == 'DELETE'
    )
    if is_delete:
        db.session.delete(s)
        db.session.commit()
        if request.method == 'DELETE':
            return '', 204
        return redirect(url_for('searches_list'))
    if request.method == 'POST':
        abort(405)
    results = s.results.all()
    return render_template('search_detail.html', search=s, results=results)


@app.route('/searches/<int:search_id>/status', methods=['GET'])
@require_auth
def searches_status(search_id):
    s = _owned_search_or_404(search_id)
    return jsonify({
        'status': s.status,
        'count': s.results.count(),
        'error': s.error,
    })


@app.route('/searches/<int:search_id>/refresh', methods=['POST'])
@require_auth
def searches_refresh(search_id):
    s = _owned_search_or_404(search_id)
    s.status = 'pending'
    s.error = None
    db.session.commit()
    fetch_search_results.delay(s.id)
    return redirect(url_for('searches_detail', search_id=s.id))


@app.route('/searches/<int:search_id>/enrichment-status', methods=['GET'])
@require_auth
def enrichment_status(search_id):
    s = _owned_search_or_404(search_id)
    total = s.results.count()
    enriched = s.results.filter(SearchResult.enrichment_json.isnot(None)).count()
    return jsonify({'total': total, 'enriched': enriched, 'pending': total - enriched})


@app.route('/searches/<int:search_id>/enrichments', methods=['GET'])
@require_auth
def list_enrichments(search_id):
    s = _owned_search_or_404(search_id)
    rows = s.results.filter(SearchResult.enrichment_json.isnot(None)).all()
    return jsonify([{'id': r.id, 'enrichment_json': r.enrichment_json} for r in rows])


@app.route('/searches/<int:search_id>/results/<int:rid>/enrich', methods=['POST'])
@require_auth
def enrich_result(search_id, rid):
    s = _owned_search_or_404(search_id)
    r = SearchResult.query.filter_by(id=rid, search_id=s.id).first_or_404()
    fetch_enrichment.delay(r.id)
    return jsonify({'status': 'queued'})


@app.route('/searches/<int:search_id>/results/<int:rid>', methods=['PATCH'])
@require_auth
def searches_toggle_result(search_id, rid):
    s = _owned_search_or_404(search_id)
    r = SearchResult.query.filter_by(id=rid, search_id=s.id).first_or_404()
    data = request.get_json(silent=True) or {}
    if 'included' in data:
        r.included = bool(data['included'])
    else:
        r.included = not r.included
    db.session.commit()
    return jsonify({'id': r.id, 'included': r.included})


# === ODS Export ===

@app.route('/searches/<int:search_id>/export/ods', methods=['POST'])
@require_auth
def export_ods(search_id):
    s = _owned_search_or_404(search_id)
    task = generate_ods_task.delay(s.id)
    return redirect(url_for('export_ods_wait', search_id=s.id, task_id=task.id))


@app.route('/searches/<int:search_id>/export/ods/wait/<task_id>')
@require_auth
def export_ods_wait(search_id, task_id):
    _owned_search_or_404(search_id)
    return render_template('export_wait.html', task_id=task_id, search_id=search_id)


@app.route('/searches/<int:search_id>/export/ods/status/<task_id>')
@require_auth
def export_ods_status(search_id, task_id):
    _owned_search_or_404(search_id)
    result = generate_ods_task.AsyncResult(task_id)
    if result.state == 'SUCCESS':
        return jsonify({'status': 'SUCCESS'})
    if result.state == 'FAILURE':
        return jsonify({'status': 'FAILURE', 'error': str(result.info)})
    return jsonify({'status': result.state})


@app.route('/searches/<int:search_id>/export/ods/download/<task_id>')
@require_auth
def export_ods_download(search_id, task_id):
    _owned_search_or_404(search_id)
    result = generate_ods_task.AsyncResult(task_id)
    if result.state != 'SUCCESS':
        return redirect(url_for('export_ods_wait', search_id=search_id, task_id=task_id))
    data = result.get()
    buf = io.BytesIO(base64.b64decode(data['ods_b64']))
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/vnd.oasis.opendocument.spreadsheet',
        as_attachment=True,
        download_name=data['filename']
    )


# === XLSX Export ===

@app.route('/searches/<int:search_id>/export/xlsx', methods=['POST'])
@require_auth
def export_xlsx(search_id):
    s = _owned_search_or_404(search_id)
    task = generate_xlsx_task.delay(s.id)
    return redirect(url_for('export_xlsx_wait', search_id=s.id, task_id=task.id))


@app.route('/searches/<int:search_id>/export/xlsx/wait/<task_id>')
@require_auth
def export_xlsx_wait(search_id, task_id):
    _owned_search_or_404(search_id)
    return render_template('export_wait.html', task_id=task_id, search_id=search_id, export_type='xlsx')


@app.route('/searches/<int:search_id>/export/xlsx/status/<task_id>')
@require_auth
def export_xlsx_status(search_id, task_id):
    _owned_search_or_404(search_id)
    result = generate_xlsx_task.AsyncResult(task_id)
    if result.state == 'SUCCESS':
        return jsonify({'status': 'SUCCESS'})
    if result.state == 'FAILURE':
        return jsonify({'status': 'FAILURE', 'error': str(result.info)})
    return jsonify({'status': result.state})


@app.route('/searches/<int:search_id>/export/xlsx/download/<task_id>')
@require_auth
def export_xlsx_download(search_id, task_id):
    _owned_search_or_404(search_id)
    result = generate_xlsx_task.AsyncResult(task_id)
    if result.state != 'SUCCESS':
        return redirect(url_for('export_xlsx_wait', search_id=search_id, task_id=task_id))
    data = result.get()
    buf = io.BytesIO(base64.b64decode(data['xlsx_b64']))
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=data['filename']
    )


# === CSV Export ===

@app.route('/searches/<int:search_id>/export/csv', methods=['POST'])
@require_auth
def export_csv(search_id):
    s = _owned_search_or_404(search_id)
    task = generate_csv_task.delay(s.id)
    return redirect(url_for('export_csv_wait', search_id=s.id, task_id=task.id))


@app.route('/searches/<int:search_id>/export/csv/wait/<task_id>')
@require_auth
def export_csv_wait(search_id, task_id):
    _owned_search_or_404(search_id)
    return render_template('export_wait.html', task_id=task_id, search_id=search_id, export_type='csv')


@app.route('/searches/<int:search_id>/export/csv/status/<task_id>')
@require_auth
def export_csv_status(search_id, task_id):
    _owned_search_or_404(search_id)
    result = generate_csv_task.AsyncResult(task_id)
    if result.state == 'SUCCESS':
        return jsonify({'status': 'SUCCESS'})
    if result.state == 'FAILURE':
        return jsonify({'status': 'FAILURE', 'error': str(result.info)})
    return jsonify({'status': result.state})


@app.route('/searches/<int:search_id>/export/csv/download/<task_id>')
@require_auth
def export_csv_download(search_id, task_id):
    _owned_search_or_404(search_id)
    result = generate_csv_task.AsyncResult(task_id)
    if result.state != 'SUCCESS':
        return redirect(url_for('export_csv_wait', search_id=search_id, task_id=task_id))
    data = result.get()
    buf = io.BytesIO(base64.b64decode(data['csv_b64']))
    buf.seek(0)
    return send_file(
        buf,
        mimetype='text/csv',
        as_attachment=True,
        download_name=data['filename']
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
