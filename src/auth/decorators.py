"""
Authentication Decorators
"""
from functools import wraps
from flask import request, jsonify, session, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime, timedelta


def require_auth(f):
    """Decorator that requires user to be authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            from src.auth.models import UserSession
            from src.db import db
            
            session_obj = UserSession.query.filter_by(token=token, is_active=True).first()
            
            if session_obj:
                if session_obj.is_expired:
                    return jsonify({'error': 'Token expired'}), 401
                
                session_obj.expires_at = datetime.utcnow() + timedelta(hours=24)
                db.session.commit()
                
                from flask_login import login_user
                from src.auth.models import User
                user = User.query.get(session_obj.user_id)
                if user and user.is_active:
                    login_user(user, remember=True)
                    return f(*args, **kwargs)
        
        if session.get('user_id'):
            from src.auth.models import User
            user = User.query.get(session.get('user_id'))
            if user and user.is_active:
                from flask_login import login_user
                login_user(user, remember=True)
                return f(*args, **kwargs)
        
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        else:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
    
    return decorated_function


def require_role(*roles):
    """Decorator that requires user to have one of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                else:
                    flash('Por favor, faça login.', 'warning')
                    return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                else:
                    flash('Você não tem permissão para acessar esta função.', 'error')
                    return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_api_key(f):
    """Decorator for API routes that require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        from src.auth.utils import hash_api_key
        from src.auth.models import ApiKey
        
        api_key_hash = hash_api_key(api_key)
        api_key_obj = ApiKey.query.filter_by(api_key_hash=api_key_hash, is_active=True).first()
        
        if not api_key_obj:
            return jsonify({'error': 'Invalid API key'}), 401
        
        api_key_obj.last_used = datetime.utcnow()
        from src.db import db
        db.session.commit()
        
        return f(*args, **kwargs)
    return decorated_function
