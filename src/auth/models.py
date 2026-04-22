"""
User Models for Authentication
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB
from src.db import db


def _utcnow():
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    """User model with secure password storage"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    last_login = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')

    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    api_keys = db.relationship('ApiKey', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def get_id(self):
        return str(self.id)


class UserSession(db.Model):
    """Session tracking for security"""
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(512), unique=True, nullable=False, index=True)
    refresh_token = db.Column(db.String(512), unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Session {self.id} for User {self.user_id}>'

    @property
    def is_expired(self):
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return _utcnow() > expires


class ApiKey(db.Model):
    """API Keys for external access"""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    api_key_hash = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(100))
    rate_limit_override = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    last_used = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ApiKey {self.id} for User {self.user_id}>'


class Search(db.Model):
    __tablename__ = 'searches'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(200))
    cnpj = db.Column(db.String(20), nullable=False)
    pregao_filter = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending', nullable=False)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    results = db.relationship(
        'SearchResult',
        backref='search',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='SearchResult.data.desc()',
    )

    def __repr__(self):
        return f'<Search {self.id} u={self.user_id} {self.status}>'


class SearchResult(db.Model):
    __tablename__ = 'search_results'

    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('searches.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    documento = db.Column(db.String(100), nullable=False)
    documento_resumido = db.Column(db.String(100))
    data = db.Column(db.Date)
    valor = db.Column(db.Numeric(15, 2))
    orgao = db.Column(db.String(200))
    codigo_orgao = db.Column(db.String(20))
    ug = db.Column(db.String(200))
    codigo_ug = db.Column(db.String(20))
    numero_processo = db.Column(db.String(100))
    observacao = db.Column(db.Text)
    categoria = db.Column(db.String(200))
    grupo = db.Column(db.String(200))
    elemento = db.Column(db.String(200))
    included = db.Column(db.Boolean, default=True, nullable=False)
    raw_json = db.Column(JSONB)
    detail_json = db.Column(JSONB)
    enrichment_json = db.Column(JSONB)
    enriched_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        db.UniqueConstraint('search_id', 'documento', name='uq_search_doc'),
    )

    def __repr__(self):
        return f'<SearchResult {self.id} doc={self.documento}>'
