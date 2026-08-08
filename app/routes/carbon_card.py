import json
import secrets
import requests
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product
from app.models.carbon_card import CarbonCard
from app.services.ollama_service import generate_carbon_breakdown

bp = Blueprint('carbon_card', __name__, url_prefix='/carbon')


def _stages_to_dicts(product):
    stage_order = {
        "raw_material": 0,
        "processing": 1,
        "manufacturing": 2,
        "shipping": 3,
    }

    result = []

    for s in sorted(
        product.stages,
        key=lambda x: (
            stage_order.get(x.stage_type, 99),
            x.order
        )
    ):
        result.append({
            "stage_type": s.stage_type,
            "name": s.name,
            "origin": s.origin,
            "transport_mode": s.transport_mode,
            "distance_km": s.distance_km,
            "description": s.description,
            "courier": s.courier,
            "shipping_type": s.shipping_type,
            "shipping_zones": s.shipping_zones,
            "dispatch_city": s.dispatch_city,
        })

    return result


@bp.route('/generate/<int:product_id>', methods=['POST'])
@login_required
def generate(product_id):
    """
    Called when the user confirms on the preview modal.
    Sends data to Ollama, stores result, redirects to the card view.
    """
    product = Product.query.filter_by(
        id=product_id, user_id=current_user.id
    ).first_or_404()

    stages = _stages_to_dicts(product)

    try:
        breakdown = generate_carbon_breakdown(
            product.name,
            product.description or "",
            stages
        )
    except requests.exceptions.ConnectionError:
        flash(
            "Could not connect to Ollama. Make sure it is running: ollama serve",
            "error"
        )
        return redirect(url_for('products.supply_chain', product_id=product_id))
    except requests.exceptions.Timeout:
        flash(
            "Ollama took too long to respond. Try a smaller model or increase REQUEST_TIMEOUT in ollama_service.py.",
            "error"
        )
        return redirect(url_for('products.supply_chain', product_id=product_id))
    except Exception as e:
        flash(f"Carbon analysis failed: {e}", "error")
        return redirect(url_for('products.supply_chain', product_id=product_id))

    # Upsert — regenerating replaces the old card
    card = CarbonCard.query.filter_by(product_id=product.id).first()
    if not card:
        card = CarbonCard(product_id=product.id, share_token=secrets.token_urlsafe(32))
        db.session.add(card)

    card.breakdown_json = json.dumps(breakdown)
    card.total_credits  = breakdown.get("total_carbon_credits_kg_co2e", 0.0)
    card.rating         = breakdown.get("rating", "—")

    db.session.commit()
    flash("Carbon card generated successfully.", "success")
    return redirect(url_for('carbon_card.view', product_id=product.id))


@bp.route('/card/<int:product_id>')
@login_required
def view(product_id):
    """Authenticated card view — accessible from dashboard and product page."""
    product = Product.query.filter_by(
        id=product_id, user_id=current_user.id
    ).first_or_404()

    card = CarbonCard.query.filter_by(product_id=product.id).first_or_404()
    breakdown = json.loads(card.breakdown_json)

    share_url = (
    f"http://{current_app.config['LAN_IP']}:5000"
    + url_for(
        "carbon_card.public",
        token=card.share_token
    )
)

    return render_template(
        'products/carbon_card.html',
        product=product,
        card=card,
        breakdown=breakdown,
        share_url=share_url,
        is_public=False
    )


@bp.route('/share/<token>')
def public(token):
    """
    Public, no-login-required page linked from the QR code.
    Shows the card to anyone who scans. Increments the product scan count.
    """
    card = CarbonCard.query.filter_by(share_token=token).first_or_404()
    product = card.product

    # Count every QR scan
    product.scan_count = (product.scan_count or 0) + 1
    db.session.commit()

    breakdown = json.loads(card.breakdown_json)

    share_url = (
    f"http://{current_app.config['LAN_IP']}:5000"
    + url_for(
        "carbon_card.public",
        token=card.share_token
    )
)

    return render_template(
        'products/carbon_card.html',
        product=product,
        card=card,
        breakdown=breakdown,
        share_url=share_url,
        is_public=True
    )


@bp.route('/preview/<int:product_id>')
@login_required
def preview_data(product_id):
    """JSON endpoint — returns supply chain summary for the preview modal."""
    product = Product.query.filter_by(
        id=product_id, user_id=current_user.id
    ).first_or_404()

    stages = _stages_to_dicts(product)
    complete = sum(1 for s in product.stages if s.is_complete)
    total    = len(product.stages)

    return jsonify({
        "product_name":    product.name,
        "description":     product.description,
        "complete_stages": complete,
        "total_stages":    total,
        "stages":          stages,
        "has_card":        product.carbon_card is not None,
    })