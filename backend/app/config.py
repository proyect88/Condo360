import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuracion base de la aplicacion"""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_ENV") == "development"
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///condo_services.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # Admin
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@condoservices.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123456!")

    # PWA
    PWA_NAME = os.getenv("PWA_NAME", "Condo Services 360")
    PWA_SHORT_NAME = os.getenv("PWA_SHORT_NAME", "Condo360")
    PWA_THEME_COLOR = os.getenv("PWA_THEME_COLOR", "#1a365d")
    PWA_BACKGROUND_COLOR = os.getenv("PWA_BACKGROUND_COLOR", "#ffffff")

    # Upload
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "frontend",
        "static",
        "uploads",
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}  # sin svg/gif (XSS)

    # Security
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
    REMEMBER_COOKIE_SECURE = os.getenv("REMEMBER_COOKIE_SECURE", "False") == "True"
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # sesion: 8 horas
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 7  # recordar: 7 dias

    # CORS: origenes externos permitidos para /api (vacio = solo mismo origen)
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")

    # Pagination
    ITEMS_PER_PAGE = 20

    # API
    API_RATE_LIMIT = "100/hour"


class DevelopmentConfig(Config):
    """Configuracion de desarrollo"""

    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Configuracion de produccion"""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configuracion de testing"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
