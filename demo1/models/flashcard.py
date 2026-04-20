from extensions import db
from datetime import datetime

class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='not learn')
    
    repetition = db.Column(db.Integer, default=0)
    easiness_factor = db.Column(db.Float, default=2.5)
    interval = db.Column(db.Integer, default=0)
    next_review_date = db.Column(db.DateTime, default=datetime.utcnow)

    collection = db.relationship('Collection', backref=db.backref('flashcards', lazy=True, cascade="all, delete-orphan"))