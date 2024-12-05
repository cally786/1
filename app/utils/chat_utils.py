from sqlalchemy import and_, or_
from flask_login import current_user
from app.models.chat import Chat, ChatMessage
from app import db
from flask import current_app

def get_unread_messages_count():
    """Get number of unread messages for current user"""
    if not current_user.is_authenticated:
        return 0
        
    if current_user.is_admin:
        # Para admins, contar mensajes no leídos en chats asignados o pendientes
        count = ChatMessage.query.join(Chat).filter(
            and_(
                or_(
                    Chat.admin_id == current_user.id,
                    and_(
                        Chat.status == 'Pendiente',
                        Chat.admin_id.is_(None)
                    )
                ),
                ChatMessage.is_read.is_(False),
                ChatMessage.sender_id != current_user.id
            )
        ).count()
    else:
        # Para usuarios normales, contar mensajes no leídos en sus chats
        count = ChatMessage.query.join(Chat).filter(
            and_(
                Chat.user_id == current_user.id,
                ChatMessage.is_read.is_(False),
                ChatMessage.sender_id != current_user.id
            )
        ).count()
    
    return count

def get_pending_chats_count():
    """Get number of pending chats"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return 0
    return Chat.query.filter_by(status='Pendiente').count()

def get_active_chats():
    """Get active chats for current user"""
    if not current_user.is_authenticated:
        return []
        
    if current_user.is_admin:
        chats = Chat.query.filter(
            and_(
                Chat.status != 'Cerrado',
                or_(
                    Chat.admin_id == current_user.id,
                    Chat.admin_id.is_(None)
                )
            )
        ).order_by(Chat.updated_at.desc()).all()
    else:
        chats = Chat.query.filter(
            and_(
                Chat.status != 'Cerrado',
                Chat.user_id == current_user.id
            )
        ).order_by(Chat.updated_at.desc()).all()
    
    # Agregar contador de mensajes no leídos a cada chat
    for chat in chats:
        chat.unread_count = ChatMessage.query.filter(
            and_(
                ChatMessage.chat_id == chat.id,
                ChatMessage.is_read.is_(False),
                ChatMessage.sender_id != current_user.id
            )
        ).count()
    
    return chats

def get_pending_chats():
    """Get pending chats (admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return []
    return Chat.query.filter_by(status='Pendiente').order_by(Chat.created_at.desc()).all()
