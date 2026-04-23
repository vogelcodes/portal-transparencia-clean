"""
Portal da Transparência - SaaS
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, abort
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import io
import base64
import os

from src.tasks import generate_ods_task, generate_xlsx_task, generate_csv_task, fetch_search_results, fetch_enrichment
from src.db import db
from src.auth import auth_bp
from src.auth.models import User, Search, SearchResult, UserUasg, Arp
from src.auth.decorators import require_auth

# Configure static folder for design system CSS
static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
app = Flask(__name__, static_folder=static_folder_path, static_url_path='/static')

_secret_key = os.getenv('SECRET_KEY')
if not _secret_key or _secret_key == 'dev':
    raise RuntimeError("SECRET_KEY env var is required and must not be 'dev'")
app.config['SECRET_KEY'] = _secret_key

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', '')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('APP_ENV') == 'production'
app.config['WTF_CSRF_TIME_LIMIT'] = None

db.init_app(app)
migrate_ext = Migrate(app, db)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth_bp)

# Login/register submit as JSON via fetch() without a prior session, so CSRF
# tokens cannot be bound. Brute-force protection (Redis) covers login abuse;
# register rate-limit is handled by upstream proxy in production.
from src.auth.routes import login as _login_view, register as _register_view  # noqa: E402
csrf.exempt(_login_view)
csrf.exempt(_register_view)


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
@require_auth
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


@app.route('/dashboard', methods=['GET'])
@require_auth
def dashboard():
    uasgs = (UserUasg.query
             .filter_by(user_id=current_user.id)
             .order_by(UserUasg.is_primary.desc(), UserUasg.created_at)
             .all())
    from src.auth.models import ArpItem, ArpEmpenho
    uasg_stats = []
    for u in uasgs:
        arp_count = u.arps.count()
        item_count = (db.session.query(db.func.count(ArpItem.id))
                      .join(Arp, ArpItem.arp_id == Arp.id)
                      .filter(Arp.user_uasg_id == u.id).scalar()) or 0
        empenho_count = (db.session.query(db.func.count(ArpEmpenho.id))
                         .join(ArpItem, ArpEmpenho.arp_item_id == ArpItem.id)
                         .join(Arp, ArpItem.arp_id == Arp.id)
                         .filter(Arp.user_uasg_id == u.id).scalar()) or 0
        uasg_stats.append({
            'u': u,
            'arp_count': arp_count,
            'item_count': item_count,
            'empenho_count': empenho_count,
        })
    searches = (Search.query
                .filter_by(user_id=current_user.id)
                .order_by(Search.created_at.desc())
                .limit(10)
                .all())
    return render_template('dashboard.html', uasg_stats=uasg_stats, searches=searches)


@app.route('/uasg/<int:uasg_id>', methods=['GET'])
@require_auth
def uasg_detail(uasg_id):
    from src.auth.models import ArpItem
    u = UserUasg.query.filter_by(id=uasg_id, user_id=current_user.id).first_or_404()
    arps = (Arp.query.filter_by(user_uasg_id=u.id)
            .order_by(Arp.data_vigencia_inicial.desc().nullslast())
            .all())
    arp_data = []
    for arp in arps:
        items_with_emps = []
        for item in arp.items.order_by(ArpItem.numero_item).all():
            emps = item.empenhos.all()
            if emps:
                items_with_emps.append({'item': item, 'emps': emps})
        arp_data.append({'arp': arp, 'itens': items_with_emps})
    return render_template('uasg_detail.html', u=u, arp_data=arp_data)


@app.route('/uasg/<int:uasg_id>/status', methods=['GET'])
@require_auth
def uasg_sync_status(uasg_id):
    u = UserUasg.query.filter_by(id=uasg_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'sync_status': u.sync_status,
        'synced_at': u.synced_at.isoformat() if u.synced_at else None,
        'arp_count': u.arps.count(),
        'sync_error': u.sync_error,
    })


@app.route('/uasg/<int:uasg_id>/resync', methods=['POST'])
@require_auth
def uasg_resync(uasg_id):
    u = UserUasg.query.filter_by(id=uasg_id, user_id=current_user.id).first_or_404()
    from src.tasks import sync_uasg_data
    u.sync_status = 'pending'
    u.sync_error = None
    db.session.commit()
    sync_uasg_data.delay(u.id, full_refresh=True)
    referer = request.referrer or ''
    if '/dashboard' in referer:
        return redirect(url_for('dashboard'))
    return redirect(url_for('uasg_detail', uasg_id=u.id))


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
