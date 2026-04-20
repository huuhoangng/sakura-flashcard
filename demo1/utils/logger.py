from extensions import db
from models.action_log import ActionLog

def log_action(user_id, action_description):
    log = ActionLog(user_id=user_id, action=action_description)
    db.session.add(log)
    db.session.commit()