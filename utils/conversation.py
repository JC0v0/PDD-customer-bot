from datetime import datetime
from utils.database import db

class ConversationModel(db.Model):
    __tablename__ = 'conversations'
    
    user_id = db.Column(db.String(64), primary_key=True)
    conversation_id = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Conversation {self.user_id}>' 