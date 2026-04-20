from extensions import db

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='private')

    user = db.relationship('User', backref=db.backref('collections', lazy=True, cascade="all, delete-orphan"))