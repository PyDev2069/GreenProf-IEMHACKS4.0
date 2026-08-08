from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user, logout_user
from app.models.product import Product

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.filter_by(user_id=current_user.id)\
                            .order_by(Product.created_at.desc()).all()
    return render_template('dashboard.html', user=current_user, products=products)

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # update current_user.name / .email / password here
        # e.g. current_user.name = request.form.get('name')
        # db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('main.profile'))
    return render_template('profile.html', user=current_user)

@bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    # delete current_user and related products here
    # db.session.delete(current_user)
    # db.session.commit()
    logout_user()
    flash('Account deleted.', 'success')
    return redirect(url_for('main.home'))