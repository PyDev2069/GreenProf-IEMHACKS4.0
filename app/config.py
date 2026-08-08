import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY                     = os.getenv('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI        = os.getenv('DATABASE_URL', 'sqlite:///greenproof.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER         = os.getenv('MAIL_SERVER')
    MAIL_PORT           = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS        = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME       = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD       = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@greenproof.dev')

    FRONTEND_URL        = os.getenv('FRONTEND_URL', 'http://localhost:5000')
    RESET_TOKEN_EXPIRY  = 3600  # 1 hour in seconds
    LAN_IP = "192.168.29.32"