"""
Portal da Transparência - SaaS
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', '')

@app.route('/')
def index():
    return jsonify({
        'app': 'Portal da Transparência SaaS',
        'version': '1.0.0',
        'status': 'running',
        'env': os.getenv('APP_ENV', 'production')
    })

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
