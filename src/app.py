"""
Portal da Transparência - SaaS
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, abort
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
import io
import base64
import os
import threading
import time

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


# === SPA cache (in-memory TTL) ===

SPA_CACHE_TTL_SECONDS = int(os.getenv('SPA_CACHE_TTL_SECONDS', '30'))
_spa_cache = {}
_spa_cache_lock = threading.Lock()


def _spa_cache_key(*parts):
    return ':'.join(str(p) for p in parts)


def _spa_cache_get(key):
    now = time.monotonic()
    with _spa_cache_lock:
        entry = _spa_cache.get(key)
        if not entry:
            return None
        if entry['expires_at'] <= now:
            _spa_cache.pop(key, None)
            return None
        return entry['value']


def _spa_cache_set(key, value, ttl=SPA_CACHE_TTL_SECONDS):
    with _spa_cache_lock:
        _spa_cache[key] = {
            'value': value,
            'expires_at': time.monotonic() + ttl,
        }


def _spa_cache_invalidate_for_user(user_id):
    prefix = f'{user_id}:'
    with _spa_cache_lock:
        for key in list(_spa_cache.keys()):
            if key.startswith(prefix):
                _spa_cache.pop(key, None)


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
    return redirect(url_for('spav2_shell'))


@app.route('/SPA', methods=['GET'])
@require_auth
def spa_shell():
    return render_template('spa.html')


@app.route('/SPAv2', methods=['GET'])
@require_auth
def spav2_shell():
    uasgs = (UserUasg.query
             .filter_by(user_id=current_user.id)
             .order_by(UserUasg.is_primary.desc(), UserUasg.created_at)
             .all())
    selected_id = request.args.get('uasg', type=int)
    if selected_id:
        selected = next((u for u in uasgs if u.id == selected_id), None)
    else:
        selected = uasgs[0] if uasgs else None
    payload = _build_uasg_payload(current_user.id, selected.id) if selected else None
    uasg_options = [{
        'id': u.id,
        'codigo_uasg': u.codigo_uasg,
        'nome_uasg': u.nome_uasg,
    } for u in uasgs]
    return render_template(
        'spav2.html',
        payload=payload,
        uasg_options=uasg_options,
        selected_id=selected.id if selected else None,
    )


def _fmt_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _build_dashboard_payload(user_id):
    from src.auth.models import ArpItem, ArpEmpenho

    uasgs = (UserUasg.query
             .filter_by(user_id=user_id)
             .order_by(UserUasg.is_primary.desc(), UserUasg.created_at)
             .all())

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
            'id': u.id,
            'codigo_uasg': u.codigo_uasg,
            'nome_uasg': u.nome_uasg,
            'sigla_uf': u.sigla_uf,
            'nome_municipio': u.nome_municipio,
            'cnpj': u.cnpj,
            'sync_status': u.sync_status,
            'sync_error': u.sync_error,
            'synced_at': _fmt_dt(u.synced_at),
            'arp_count': arp_count,
            'item_count': item_count,
            'empenho_count': empenho_count,
        })

    searches = (Search.query
                .filter_by(user_id=user_id)
                .order_by(Search.created_at.desc())
                .limit(20)
                .all())
    search_rows = [{
        'id': s.id,
        'name': s.name,
        'cnpj': s.cnpj,
        'pregao_filter': s.pregao_filter,
        'status': s.status,
        'error': s.error,
        'created_at': _fmt_dt(s.created_at),
        'updated_at': _fmt_dt(s.updated_at),
        'results_count': s.results.count(),
    } for s in searches]

    return {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'uasgs': uasg_stats,
        'searches': search_rows,
    }


def _build_uasg_payload(user_id, uasg_id):
    u = UserUasg.query.filter_by(id=uasg_id, user_id=user_id).first_or_404()
    arps = (Arp.query.filter_by(user_uasg_id=u.id)
            .order_by(Arp.data_vigencia_inicial.desc().nullslast())
            .all())

    arp_rows = []
    for arp in arps:
        item_rows = []
        total_qty_hom = 0.0
        total_qty_emp = 0.0

        for item in arp.items.order_by('numero_item').all():
            raw_item = item.raw_json or {}
            qty_hom = float(raw_item.get('quantidadeHomologadaItem') or 0)
            qty_emp = 0.0
            empenho_rows = []

            for emp in item.empenhos.order_by('id').all():
                raw_emp = emp.raw_json or {}
                emp_qty = float(raw_emp.get('quantidadeEmpenhada') or 0)
                qty_emp += emp_qty
                empenho_rows.append({
                    'id': emp.id,
                    'numero_empenho': emp.numero_empenho,
                    'valor': float(emp.valor) if emp.valor is not None else None,
                    'data': _fmt_dt(emp.data),
                    'unidade': raw_emp.get('unidade'),
                    'tipo': raw_emp.get('tipo'),
                    'quantidade_registrada': raw_emp.get('quantidadeRegistrada'),
                    'quantidade_empenhada': raw_emp.get('quantidadeEmpenhada'),
                    'saldo_empenho': raw_emp.get('saldoEmpenho'),
                    'data_hora_atualizacao': raw_emp.get('dataHoraAtualizacao'),
                })

            percentual = 0.0
            if qty_hom > 0:
                percentual = min(100.0, max(0.0, (qty_emp / qty_hom) * 100))

            item_rows.append({
                'id': item.id,
                'numero_item': item.numero_item,
                'descricao': item.descricao or raw_item.get('descricaoItem'),
                'quantidade_registrada': float(item.quantidade) if item.quantidade is not None else None,
                'valor_unitario': float(item.valor_unitario) if item.valor_unitario is not None else None,
                'fornecedor': raw_item.get('nomeRazaoSocialFornecedor'),
                'fornecedor_documento': raw_item.get('niFornecedor'),
                'quantidade_homologada': qty_hom,
                'quantidade_empenhada_total': qty_emp,
                'percentual_empenhado': round(percentual, 2),
                'valor_total': float(raw_item.get('valorTotal')) if raw_item.get('valorTotal') is not None else None,
                'empenhos': empenho_rows,
            })

            total_qty_hom += qty_hom
            total_qty_emp += qty_emp

        percentual_arp = 0.0
        if total_qty_hom > 0:
            percentual_arp = min(100.0, max(0.0, (total_qty_emp / total_qty_hom) * 100))

        arp_rows.append({
            'id': arp.id,
            'numero_controle_pncp_ata': arp.numero_controle_pncp_ata,
            'numero_ata_registro_preco': arp.numero_ata_registro_preco,
            'objeto': arp.objeto,
            'data_vigencia_inicial': _fmt_dt(arp.data_vigencia_inicial),
            'data_vigencia_final': _fmt_dt(arp.data_vigencia_final),
            'total_itens': len(item_rows),
            'itens_com_empenho': sum(1 for i in item_rows if i['empenhos']),
            'total_quantidade_homologada': round(total_qty_hom, 2),
            'total_quantidade_empenhada': round(total_qty_emp, 2),
            'percentual_empenhado': round(percentual_arp, 2),
            'itens': item_rows,
        })

    return {
        'uasg': {
            'id': u.id,
            'codigo_uasg': u.codigo_uasg,
            'nome_uasg': u.nome_uasg,
            'sigla_uf': u.sigla_uf,
            'nome_municipio': u.nome_municipio,
            'cnpj': u.cnpj,
            'sync_status': u.sync_status,
            'sync_error': u.sync_error,
            'synced_at': _fmt_dt(u.synced_at),
        },
        'arps': arp_rows,
    }


@app.route('/api/spa/dashboard', methods=['GET'])
@require_auth
def spa_dashboard_api():
    cache_key = _spa_cache_key(current_user.id, 'dashboard')
    cached_payload = _spa_cache_get(cache_key)
    if cached_payload is not None:
        return jsonify({**cached_payload, 'cache': {'cached': True, 'ttl_seconds': SPA_CACHE_TTL_SECONDS}})

    payload = _build_dashboard_payload(current_user.id)
    _spa_cache_set(cache_key, payload)
    return jsonify({**payload, 'cache': {'cached': False, 'ttl_seconds': SPA_CACHE_TTL_SECONDS}})


@app.route('/api/spa/uasg/<int:uasg_id>', methods=['GET'])
@require_auth
def spa_uasg_api(uasg_id):
    cache_key = _spa_cache_key(current_user.id, 'uasg', uasg_id)
    cached_payload = _spa_cache_get(cache_key)
    if cached_payload is not None:
        return jsonify({**cached_payload, 'cache': {'cached': True, 'ttl_seconds': SPA_CACHE_TTL_SECONDS}})

    payload = _build_uasg_payload(current_user.id, uasg_id)
    _spa_cache_set(cache_key, payload)
    return jsonify({**payload, 'cache': {'cached': False, 'ttl_seconds': SPA_CACHE_TTL_SECONDS}})


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
    _spa_cache_invalidate_for_user(current_user.id)
    referer = request.referrer or ''
    if '/dashboard' in referer:
        return redirect(url_for('dashboard'))
    return redirect(url_for('uasg_detail', uasg_id=u.id))


_UASG_EXPORT_TASKS = {
    'xlsx': 'export_uasg_xlsx_task',
    'csv':  'export_uasg_csv_task',
    'ods':  'export_uasg_ods_task',
}

@app.route('/uasg/<int:uasg_id>/export/<fmt>', methods=['POST'])
@require_auth
def uasg_export_start(uasg_id, fmt):
    if fmt not in _UASG_EXPORT_TASKS:
        abort(404)
    u = UserUasg.query.filter_by(id=uasg_id, user_id=current_user.id).first_or_404()
    from src.tasks import export_uasg_xlsx_task, export_uasg_csv_task, export_uasg_ods_task
    task_fn = {'xlsx': export_uasg_xlsx_task, 'csv': export_uasg_csv_task,
               'ods': export_uasg_ods_task}[fmt]
    task = task_fn.delay(u.id)
    return redirect(url_for('uasg_export_wait', uasg_id=u.id, fmt=fmt, task_id=task.id))


@app.route('/uasg/<int:uasg_id>/export/<fmt>/wait/<task_id>')
@require_auth
def uasg_export_wait(uasg_id, fmt, task_id):
    if fmt not in _UASG_EXPORT_TASKS:
        abort(404)
    UserUasg.query.filter_by(id=uasg_id, user_id=current_user.id).first_or_404()
    return render_template('uasg_export_wait.html', uasg_id=uasg_id, fmt=fmt, task_id=task_id)


@app.route('/uasg/<int:uasg_id>/export/<fmt>/status/<task_id>')
@require_auth
def uasg_export_status(uasg_id, fmt, task_id):
    if fmt not in _UASG_EXPORT_TASKS:
        abort(404)
    UserUasg.query.filter_by(id=uasg_id, user_id=current_user.id).first_or_404()
    from src.tasks import export_uasg_xlsx_task, export_uasg_csv_task, export_uasg_ods_task
    task_fn = {'xlsx': export_uasg_xlsx_task, 'csv': export_uasg_csv_task,
               'ods': export_uasg_ods_task}[fmt]
    result = task_fn.AsyncResult(task_id)
    if result.state == 'SUCCESS':
        return jsonify({'status': 'SUCCESS'})
    if result.state == 'FAILURE':
        return jsonify({'status': 'FAILURE', 'error': str(result.info)})
    return jsonify({'status': result.state})


@app.route('/uasg/<int:uasg_id>/export/<fmt>/download/<task_id>')
@require_auth
def uasg_export_download(uasg_id, fmt, task_id):
    if fmt not in _UASG_EXPORT_TASKS:
        abort(404)
    UserUasg.query.filter_by(id=uasg_id, user_id=current_user.id).first_or_404()
    from src.tasks import export_uasg_xlsx_task, export_uasg_csv_task, export_uasg_ods_task
    task_fn = {'xlsx': export_uasg_xlsx_task, 'csv': export_uasg_csv_task,
               'ods': export_uasg_ods_task}[fmt]
    result = task_fn.AsyncResult(task_id)
    if result.state != 'SUCCESS':
        return redirect(url_for('uasg_export_wait', uasg_id=uasg_id, fmt=fmt, task_id=task_id))
    data = result.get()
    buf = io.BytesIO(base64.b64decode(data['blob_b64']))
    buf.seek(0)
    return send_file(buf, mimetype=data['mimetype'], as_attachment=True,
                     download_name=data['filename'])


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
    _spa_cache_invalidate_for_user(current_user.id)
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
        _spa_cache_invalidate_for_user(current_user.id)
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
    _spa_cache_invalidate_for_user(current_user.id)
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
