from flask import Flask
from flask_cors import CORS
import os
from app.models.session import SessionManager


def _parse_cors_origins():
    raw_origins = os.environ.get('CORS_ORIGINS') or os.environ.get('FRONTEND_URL', '')
    origins = [origin.strip() for origin in raw_origins.split(',') if origin.strip()]
    return origins or '*'


def create_app():
    app = Flask(__name__)

    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['JSON_AS_ASCII'] = False

    # 启用 CORS
    CORS(app, resources={r"/api/*": {"origins": _parse_cors_origins()}})

    # 初始化数据库
    SessionManager.init_db()
    SessionManager.init_token_usage()

    # 注册蓝图
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
