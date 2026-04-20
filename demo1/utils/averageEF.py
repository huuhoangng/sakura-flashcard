from sqlalchemy import func
from extensions import db
from models.flashcard import Flashcard

def get_weighted_average_ef(vocab_word):
    """
    Calculates the repetition-weighted average EF for a specific flashcard front.
    Cards with 0 repetitions are effectively ignored in the weight.
    """
    result = db.session.query(
        func.sum(Flashcard.easiness_factor * Flashcard.repetition).label('weighted_sum'),
        func.sum(Flashcard.repetition).label('total_repetitions')
    ).filter(
        Flashcard.front.ilike(vocab_word)
    ).first()

    weighted_sum = result.weighted_sum or 0
    total_reps = result.total_repetitions or 0

    if total_reps == 0:
        return 0.0, 0.0
        
    return weighted_sum, total_reps