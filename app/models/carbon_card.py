from datetime import datetime, timezone
from app.extensions import db


class CarbonCard(db.Model):
    __tablename__ = 'carbon_cards'

    id          = db.Column(db.Integer, primary_key=True)
    product_id  = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, unique=True)
    generated_at= db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Raw JSON string from LLM parsing — list of stage breakdowns
    breakdown_json = db.Column(db.Text, nullable=False)

    # Aggregate totals (pre-computed for fast display)
    total_credits  = db.Column(db.Float, nullable=False, default=0.0)
    rating         = db.Column(db.String(10))   # A+, A, B, C, D

    # Public share token (for QR code link — no auth required)
    share_token    = db.Column(db.String(64), unique=True, nullable=False)

    product = db.relationship('Product', backref=db.backref('carbon_card', uselist=False))

    def __repr__(self):
        return f'<CarbonCard product={self.product_id} total={self.total_credits}>'
    