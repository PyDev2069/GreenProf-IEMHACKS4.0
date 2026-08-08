from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.services.auth_service import (
    hash_password, check_password,
    generate_reset_token, verify_reset_token,
    send_welcome_email, send_reset_email
)

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        # Validate
        error = None
        if not name:
            error = 'Name is required.'
        elif not email:
            error = 'Email is required.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif User.query.filter_by(email=email).first():
            error = 'An account with this email already exists.'

        if error:
            flash(error, 'error')
            return render_template('auth/signup.html', name=name, email=email)

        # Create user
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password)
        )
        db.session.add(user)
        db.session.commit()

        # Send welcome email (silently fail if mail not configured)
        try:
            send_welcome_email(user)
        except Exception:
            pass

        login_user(user)
        flash(f'Welcome to GreenProof, {user.name}!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/signup.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if not user or not check_password(password, user.password_hash):
            flash('Incorrect email or password.', 'error')
            return render_template('auth/login.html', email=email)

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.dashboard'))

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    sent = False
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Email is required.', 'error')
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                token = generate_reset_token(email)
                try:
                    send_reset_email(email, token)
                    print(f"Reset email sent to {email} with token {token}")
                except Exception as e:
                    print(f"Error sending reset email: {e}")
            # Always show sent state — don't reveal if email exists
            sent = True

    return render_template('auth/forgot_password.html', sent=sent)


@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    token = request.args.get('token') or request.form.get('token')

    if not token:
        flash('Invalid or missing reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)

        email = verify_reset_token(token)
        if not email:
            flash('This link has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.forgot_password'))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('auth.forgot_password'))

        user.password_hash = hash_password(password)
        db.session.commit()

        flash('Password updated. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    # Validate token on GET too — show error early if expired
    if not verify_reset_token(token):
        flash('This link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))

    return render_template('auth/reset_password.html', token=token)