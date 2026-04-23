"""UASG lookup and management routes"""
import json as _json
import urllib.request
import urllib.error

from flask import request, jsonify
from flask_login import current_user

from src.auth import auth_bp
from src.auth.models import UserUasg
from src.db import db

_UASG_API = "https://dadosabertos.compras.gov.br/modulo-uasg/1_consultarUasg"


def _require_auth():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    return None


@auth_bp.route('/uasg/lookup', methods=['GET'])
def uasg_lookup():
    err = _require_auth()
    if err:
        return err
    codigo = (request.args.get('codigo') or '').strip()
    if not codigo or not codigo.isdigit() or len(codigo) > 10:
        return jsonify({'error': 'Código inválido'}), 400
    url = f"{_UASG_API}?pagina=1&codigoUasg={codigo}&statusUasg=true"
    try:
        req = urllib.request.Request(url, headers={'Accept': '*/*'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = _json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return jsonify({'error': f'API retornou {e.code}'}), 502
    except Exception:
        return jsonify({'error': 'Falha ao consultar API'}), 502
    resultado = data.get('resultado') or []
    if not resultado:
        return jsonify({'found': False}), 200
    r = resultado[0]
    return jsonify({
        'found': True,
        'codigoUasg': r.get('codigoUasg'),
        'nomeUasg': r.get('nomeUasg'),
        'siglaUf': r.get('siglaUf'),
        'nomeMunicipio': r.get('nomeMunicipioIbge'),
        'cnpj': r.get('cnpjCpfUasg'),
    })


@auth_bp.route('/uasg', methods=['GET'])
def uasg_list():
    err = _require_auth()
    if err:
        return err
    items = (UserUasg.query
             .filter_by(user_id=current_user.id)
             .order_by(UserUasg.is_primary.desc(), UserUasg.created_at)
             .all())
    return jsonify([{
        'id': u.id,
        'codigoUasg': u.codigo_uasg,
        'nomeUasg': u.nome_uasg,
        'siglaUf': u.sigla_uf,
        'nomeMunicipio': u.nome_municipio,
        'cnpj': u.cnpj,
        'isPrimary': u.is_primary,
    } for u in items])


@auth_bp.route('/uasg', methods=['POST'])
def uasg_save():
    err = _require_auth()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    codigo = (data.get('codigoUasg') or '').strip()
    if not codigo or not codigo.isdigit():
        return jsonify({'error': 'Código inválido'}), 400
    if UserUasg.query.filter_by(user_id=current_user.id, codigo_uasg=codigo).first():
        return jsonify({'error': 'UASG já cadastrada'}), 409
    is_first = UserUasg.query.filter_by(user_id=current_user.id).count() == 0
    uasg = UserUasg(
        user_id=current_user.id,
        codigo_uasg=codigo,
        nome_uasg=data.get('nomeUasg'),
        sigla_uf=data.get('siglaUf'),
        nome_municipio=data.get('nomeMunicipio'),
        cnpj=data.get('cnpj'),
        is_primary=is_first,
    )
    db.session.add(uasg)
    db.session.commit()

    from src.tasks import sync_uasg_data
    sync_uasg_data.delay(uasg.id)

    return jsonify({'id': uasg.id, 'codigoUasg': uasg.codigo_uasg}), 201


@auth_bp.route('/uasg/<int:uasg_id>', methods=['DELETE'])
def uasg_delete(uasg_id):
    err = _require_auth()
    if err:
        return err
    uasg = UserUasg.query.filter_by(id=uasg_id, user_id=current_user.id).first_or_404()
    db.session.delete(uasg)
    db.session.commit()
    return '', 204
