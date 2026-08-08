from app.extensions import db

STAGE_LABELS = {
    'raw_material':  'Raw Material',
    'processing':    'Processing',
    'manufacturing': 'Manufacturing',
    'shipping':      'Shipping',
}

class Stage(db.Model):
    __tablename__ = 'stages'

    id             = db.Column(db.Integer, primary_key=True)
    product_id     = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stage_type     = db.Column(db.String(50), nullable=False)
    order          = db.Column(db.Integer, nullable=False, default=1)
    name           = db.Column(db.String(200))
    description    = db.Column(db.Text)
    origin         = db.Column(db.String(200))
    transport_mode = db.Column(db.String(100))
    distance_km    = db.Column(db.Float)
    # Shipping-specific
    courier        = db.Column(db.String(200))
    shipping_type  = db.Column(db.String(100))
    shipping_zones = db.Column(db.String(200))
    dispatch_city  = db.Column(db.String(200))
    is_complete    = db.Column(db.Boolean, default=False)

    @property
    def label(self):
        return STAGE_LABELS.get(self.stage_type, self.stage_type)

    def __repr__(self):
        return f'<Stage {self.stage_type} #{self.id}>'