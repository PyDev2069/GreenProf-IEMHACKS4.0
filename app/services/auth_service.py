import bcrypt
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_mail import Message
from app.extensions import mail


# ── Password ──────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Reset token ───────────────────────────────────────────

def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def generate_reset_token(email: str) -> str:
    return _serializer().dumps(email, salt='password-reset')

def verify_reset_token(token: str):
    try:
        return _serializer().loads(
            token,
            salt='password-reset',
            max_age=current_app.config['RESET_TOKEN_EXPIRY']
        )
    except Exception:
        return None


# ── Emails ────────────────────────────────────────────────

def send_welcome_email(user):
    msg = Message(
        subject='Welcome to GreenProof 🌱',
        recipients=[user.email],
        html=f"""
<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:520px;margin:40px auto;color:#0a0a0a;">
  <h2 style="font-size:24px;margin-bottom:8px;">Welcome, {user.name}.</h2>
  <p style="color:#555;line-height:1.6;">
    Your GreenProof account is ready. You can now start mapping your
    product supply chains and generating verified eco-labels.
  </p>
  <a href="{current_app.config['FRONTEND_URL']}/dashboard"
     style="display:inline-block;margin-top:24px;padding:12px 28px;
            background:#0a0a0a;color:#fff;text-decoration:none;
            border-radius:4px;font-size:14px;">
    Go to your dashboard
  </a>
  <p style="margin-top:40px;font-size:12px;color:#aaa;">
    — The GreenProof Team
  </p>
</body>
</html>
"""
    )
    mail.send(msg)


def send_reset_email(email: str, token: str):
    link = f"{current_app.config['FRONTEND_URL']}/auth/reset-password?token={token}"
    msg  = Message(
        subject='Reset your GreenProof password',
        recipients=[email],
        html=f"""
<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:520px;margin:40px auto;color:#0a0a0a;">
  <h2 style="font-size:24px;margin-bottom:8px;">Reset your password</h2>
  <p style="color:#555;line-height:1.6;">
    Someone requested a password reset for your GreenProof account.
    Click below to set a new one. This link expires in 1 hour.
  </p>
  <a href="{link}"
     style="display:inline-block;margin-top:24px;padding:12px 28px;
            background:#0a0a0a;color:#fff;text-decoration:none;
            border-radius:4px;font-size:14px;">
    Reset password
  </a>
  <p style="margin-top:24px;font-size:12px;color:#aaa;">
    If you didn't request this, ignore this email.
  </p>
</body>
</html>
"""
    )
    mail.send(msg)