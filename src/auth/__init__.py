"""
Authentication Module
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from src.auth import routes, models, utils, decorators, uasg
