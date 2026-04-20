from datetime import datetime, timedelta

def calculate_sm2(quality, repetition, easiness_factor, interval):
    """
    quality: 0-5 scale (0 = blackout, 5 = perfect response)
    """
    if quality >= 3:
        if repetition == 0:
            interval = 1
        elif repetition == 1:
            interval = 6
        else:
            interval = round(interval * easiness_factor)
        repetition += 1
    else:
        repetition = 0
        interval = 1
    
    easiness_factor = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if easiness_factor < 1.3:
        easiness_factor = 1.3
        
    next_review_date = datetime.utcnow() + timedelta(days=interval)
    
    return repetition, easiness_factor, interval, next_review_date