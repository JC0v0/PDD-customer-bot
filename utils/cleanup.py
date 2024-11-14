from database import db
from utils.conversation import ConversationModel
from datetime import datetime, timedelta

def cleanup_expired_conversations():
    """清理过期的对话记录"""
    with db.get_app().app_context():
        expire_date = datetime.now() - timedelta(days=180)
        ConversationModel.query.filter(ConversationModel.timestamp < expire_date).delete()
        db.session.commit() 