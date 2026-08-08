from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product
from app.models.stage import Stage

bp = Blueprint('products', __name__, url_prefix='/products')

STAGE_ORDER = ['raw_material', 'processing', 'manufacturing', 'shipping']


def _next_order(product_id, stage_type):
    existing = Stage.query.filter_by(
        product_id=product_id, stage_type=stage_type
    ).count()
    return existing + 1


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Product name is required.', 'error')
            return render_template('products/add.html')

        product = Product(
            user_id=current_user.id,
            name=name,
            description=description
        )
        db.session.add(product)
        db.session.flush()

        for i, stage_type in enumerate(STAGE_ORDER):
            stage = Stage(
                product_id=product.id,
                stage_type=stage_type,
                order=1
            )
            db.session.add(stage)

        db.session.commit()
        flash(f'"{name}" created. Now build its supply chain.', 'success')
        return redirect(url_for('products.supply_chain', product_id=product.id))

    return render_template('products/add.html')


@bp.route('/<int:product_id>/supply-chain', methods=['GET', 'POST'])
@login_required
def supply_chain(product_id):
    product = Product.query.filter_by(
        id=product_id, user_id=current_user.id
    ).first_or_404()

    if request.method == 'POST':
        action   = request.form.get('action')
        stage_id = request.form.get('stage_id', type=int)

        if action == 'save':
            stage = Stage.query.filter_by(
                id=stage_id, product_id=product.id
            ).first_or_404()

            stage.name           = request.form.get('name', '').strip()
            stage.description    = request.form.get('description', '').strip()
            stage.origin         = request.form.get('origin', '').strip()
            stage.transport_mode = request.form.get('transport_mode', '').strip()
            distance             = request.form.get('distance_km', '').strip()
            stage.distance_km    = float(distance) if distance else None

            if stage.stage_type == 'shipping':
                stage.courier        = request.form.get('courier', '').strip()
                stage.shipping_type  = request.form.get('shipping_type', '').strip()
                stage.shipping_zones = request.form.get('shipping_zones', '').strip()
                stage.dispatch_city  = request.form.get('dispatch_city', '').strip()

            stage.is_complete = True
            db.session.commit()
            flash(f'{stage.label} stage saved.', 'success')

        elif action == 'add_block':
            stage_type = request.form.get('stage_type')
            if stage_type in ['raw_material', 'processing', 'manufacturing']:
                order = _next_order(product.id, stage_type)
                new_stage = Stage(
                    product_id=product.id,
                    stage_type=stage_type,
                    order=order
                )
                db.session.add(new_stage)
                db.session.commit()
                flash(f'New block added.', 'success')

        elif action == 'delete_block':
            stage = Stage.query.filter_by(
                id=stage_id, product_id=product.id
            ).first_or_404()
            label = stage.label
            db.session.delete(stage)
            db.session.commit()
            flash(f'{label} block removed.', 'success')

        return redirect(url_for('products.supply_chain', product_id=product.id))

    stages_grouped = {t: [] for t in STAGE_ORDER}
    for stage in sorted(product.stages, key=lambda s: s.order):
        if stage.stage_type in stages_grouped:
            stages_grouped[stage.stage_type].append(stage)

    return render_template('products/supply_chain.html',
                           product=product,
                           stages_grouped=stages_grouped,
                           stage_order=STAGE_ORDER)


# ── NEW — reorder endpoint called by drag and drop JS ──
@bp.route('/<int:product_id>/reorder', methods=['POST'])
@login_required
def reorder(product_id):
    """
    Receives JSON: { "stage_type": "processing", "order": [3, 1, 5] }
    where order is a list of stage IDs in the new sequence.
    Updates the `order` column on each stage.
    """
    product = Product.query.filter_by(
        id=product_id, user_id=current_user.id
    ).first_or_404()

    data       = request.get_json()
    stage_type = data.get('stage_type')
    id_order   = data.get('order', [])  # list of stage IDs in new order

    if not stage_type or not id_order:
        return jsonify({'error': 'Invalid payload'}), 400

    # Validate all IDs belong to this product and stage_type
    stages = Stage.query.filter(
        Stage.id.in_(id_order),
        Stage.product_id == product.id,
        Stage.stage_type == stage_type
    ).all()

    if len(stages) != len(id_order):
        return jsonify({'error': 'Stage mismatch'}), 400

    # Apply new order
    stage_map = {s.id: s for s in stages}
    for position, stage_id in enumerate(id_order, start=1):
        stage_map[stage_id].order = position

    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
def delete(product_id):
    product = Product.query.filter_by(
        id=product_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(product)
    db.session.commit()
    flash(f'"{product.name}" deleted.', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/<int:product_id>/scan', methods=['POST'])
@login_required
def scan(product_id):
    """Increment scan count for a product. Called from the supply chain page."""
    product = Product.query.filter_by(
        id=product_id, user_id=current_user.id
    ).first_or_404()
    product.scan_count = (product.scan_count or 0) + 1
    db.session.commit()
    return jsonify({'ok': True, 'scan_count': product.scan_count})
