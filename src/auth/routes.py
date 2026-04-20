"""
Authentication Routes
"""
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from datetime import datetime, timedelta, timezone
import re

from src.auth import auth_bp
from src.auth.models import User, UserSession
from flask import current_app
from src.auth.utils import (
    generate_salt, hash_password, verify_password,
    generate_jwt, validate_password_strength,
    RateLimiter, sanitize_username, sanitize_email
)
from src.db import db


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json() if request.is_json else request.form
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    errors = []
    
    if not username or len(username) < 3:
        errors.append('O usuário deve ter pelo menos 3 caracteres.')
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append('O usuário deve conter apenas letras, números e underscore.')
    
    if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        errors.append('Email inválido.')
    
    is_valid, msg = validate_password_strength(password)
    if not is_valid:
        errors.append(msg)
    
    if password != confirm_password:
        errors.append('As senhas não coincidem.')
    
    if User.query.filter_by(username=sanitize_username(username)).first():
        errors.append('Este usuário já existe.')
    
    if User.query.filter_by(email=sanitize_email(email)).first():
        errors.append('Este email já está cadastrado.')
    
    if errors:
        if request.is_json:
            return jsonify({'success': False, 'errors': errors}), 400
        for error in errors:
            flash(error, 'error')
        return render_template('register.html', username=username, email=email), 400
    
    try:
        salt = generate_salt()
        password_hash = hash_password(password, salt)
        
        user = User(
            username=sanitize_username(username),
            email=sanitize_email(email),
            salt=salt,
            password_hash=password_hash,
            created_at=datetime.now(timezone.utc),
            is_active=True,
            role='user'
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': 'Conta criada com sucesso!',
                'redirect': url_for('auth.login')
            }), 201
        
        return redirect(url_for('auth.login'))
        
    except Exception:
        db.session.rollback()
        flash('Erro ao criar conta. Tente novamente.', 'error')
        if request.is_json:
            return jsonify({'success': False, 'errors': ['Erro interno.']}), 500
        return render_template('register.html'), 500


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() if request.is_json else request.form
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)
    
    rate_limiter = RateLimiter()
    identifier = f"login_{username}"
    
    if rate_limiter.is_locked_out(identifier):
        remaining = rate_limiter.get_remaining_lockout(identifier)
        msg = f'Muitos tentativas falhas. Tente novamente em {remaining} segundos.'
        if request.is_json:
            return jsonify({'success': False, 'error': msg, 'locked': True, 'retry_after': remaining}), 429
        flash(msg, 'error')
        return render_template('login.html'), 429
    
    user = User.query.filter_by(username=sanitize_username(username)).first()
    
    if not user:
        rate_limiter.record_attempt(identifier)
        if request.is_json:
            return jsonify({'success': False, 'error': 'Usuário ou senha incorretos.'}), 401
        flash('Usuário ou senha incorretos.', 'error')
        return render_template('login.html'), 401
    
    if not verify_password(password, user.salt, user.password_hash):
        rate_limiter.record_attempt(identifier)
        if request.is_json:
            return jsonify({'success': False, 'error': 'Usuário ou senha incorretos.'}), 401
        flash('Usuário ou senha incorretos.', 'error')
        return render_template('login.html'), 401
    
    if not user.is_active:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Conta desativada.'}), 403
        flash('Esta conta foi desativada.', 'error')
        return render_template('login.html'), 403
    
    rate_limiter.record_success(identifier)
    
    user.last_login = datetime.now(timezone.utc)

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24 if not remember_me else 30*24)
    token = generate_jwt(user.id, expires_at, current_app.config['SECRET_KEY'])
    
    session_obj = UserSession(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        is_active=True
    )
    
    db.session.add(session_obj)
    db.session.commit()
    
    login_user(user, remember=remember_me)
    
    session['token'] = token
    session['user_id'] = user.id
    
    next_page = request.args.get('next') or url_for('index')
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso!',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'redirect': next_page
        }), 200
    
    flash(f'Bem-vindo(a), {user.username}!', 'success')
    return redirect(next_page)


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    token = session.get('token')
    
    if token:
        session_obj = UserSession.query.filter_by(token=token).first()
        if session_obj:
            session_obj.is_active = False
            db.session.commit()
    
    logout_user()
    session.clear()
    
    flash('Você foi desconectado(a).', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/me', methods=['GET'])
def me():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None
    })


@auth_bp.route('/sessions', methods=['GET'])
def list_sessions():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    sessions = UserSession.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    return jsonify({
        'sessions': [{
            'id': s.id,
            'created_at': s.created_at.isoformat(),
            'expires_at': s.expires_at.isoformat(),
            'ip_address': s.ip_address,
            'user_agent': s.user_agent,
            'is_current': s.token == session.get('token')
        } for s in sessions]
    })


@auth_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def revoke_session(session_id):
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    session_obj = UserSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session_obj:
        return jsonify({'error': 'Session not found'}), 404
    
    session_obj.is_active = False
    db.session.commit()
    
    if session_obj.token == session.get('token'):
        logout_user()
        session.clear()
        return jsonify({'message': 'Session revoked. Logged out.', 'logged_out': True})
    
    return jsonify({'message': 'Session revoked'})


@auth_bp.route('/sessions/refresh', methods=['POST'])
def refresh_session():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    token = session.get('token')
    if not token:
        return jsonify({'error': 'No session'}), 400
    
    session_obj = UserSession.query.filter_by(token=token).first()
    if session_obj:
        session_obj.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        db.session.commit()
        return jsonify({'message': 'Session refreshed', 'expires_at': session_obj.expires_at.isoformat()})
    
    return jsonify({'error': 'Session not found'}), 404


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json() if request.is_json else request.form
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    if not verify_password(current_password, current_user.salt, current_user.password_hash):
        return jsonify({'success': False, 'error': 'Senha atual incorreta.'}), 400
    
    is_valid, msg = validate_password_strength(new_password)
    if not is_valid:
        return jsonify({'success': False, 'error': msg}), 400
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': 'As novas senhas não coincidem.'}), 400
    
    new_salt = generate_salt()
    new_hash = hash_password(new_password, new_salt)
    
    current_user.salt = new_salt
    current_user.password_hash = new_hash
    
    token = session.get('token')
    UserSession.query.filter(
        UserSession.user_id == current_user.id,
        UserSession.token != token
    ).update({'is_active': False})
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Senha alterada com sucesso!'})
