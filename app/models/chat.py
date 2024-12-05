from app import db
from datetime import datetime

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(20), default='Pendiente')  # Pendiente, Activo, Cerrado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(100), nullable=False)
    
    # Relaciones
    user = db.relationship('User', foreign_keys=[user_id], backref='user_chats')
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_chats')
    messages = db.relationship('ChatMessage', backref='chat', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Chat {self.id} - {self.status}>'

    def close(self):
        """Cierra el chat y registra la fecha de cierre"""
        self.status = 'Cerrado'
        self.closed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def assign_admin(self, admin_id):
        """Asigna un admin al chat y lo marca como activo"""
        self.admin_id = admin_id
        self.status = 'Activo'
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def add_message(self, sender_id, content):
        """Agrega un mensaje al chat y actualiza la fecha de última actualización"""
        message = ChatMessage(
            chat_id=self.id,
            sender_id=sender_id,
            content=content
        )
        db.session.add(message)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return message

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relación con el remitente
    sender = db.relationship('User', backref='sent_messages')

    def __repr__(self):
        return f'<ChatMessage {self.id} - Chat {self.chat_id}>'

    def mark_as_read(self):
        """Marca el mensaje como leído"""
        self.is_read = True
        db.session.commit()
