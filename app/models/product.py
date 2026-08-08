from datetime import datetime, timezone
from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    stages = db.relationship('Stage', backref='product',
                             lazy=True, cascade='all, delete-orphan',
                             order_by='Stage.order')

    def __repr__(self):
        return f'<Product {self.name}>'