from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_, or_
from app.models.chat import Chat, ChatMessage
from app import db
from app.utils.decorators import requires_admin
from app.utils.chat_utils import (
    get_unread_messages_count,
    get_pending_chats_count,
    get_active_chats,
    get_pending_chats
)

chat = Blueprint('chat', __name__, url_prefix='/chat')

# Make chat utilities available to all templates
@chat.app_context_processor
def inject_chat_utils():
    return {
        'injected_functions': {
            'get_unread_messages_count': get_unread_messages_count,
            'get_pending_chats_count': get_pending_chats_count,
            'get_active_chats': get_active_chats,
            'get_pending_chats': get_pending_chats
        }
    }

@chat.route('/')
@login_required
def my_chats():
    if current_user.is_admin:
        chats = Chat.query.filter(
            (Chat.admin_id == current_user.id) | 
            (Chat.status == 'Pendiente')
        ).order_by(Chat.created_at.desc()).all()
    else:
        chats = Chat.query.filter_by(user_id=current_user.id)\
            .order_by(Chat.created_at.desc()).all()
    return render_template('chat/my_chats.html', chats=chats)

@chat.route('/pending')
@login_required
@requires_admin
def pending_chats():
    chats = Chat.query.filter_by(status='Pendiente')\
        .order_by(Chat.created_at.desc()).all()
    return render_template('chat/pending_chats.html', chats=chats)

@chat.route('/new', methods=['POST'])
@login_required
def new_chat():
    title = request.form.get('title')
    if not title:
        return jsonify({'success': False, 'message': 'El título es requerido'})
    
    chat = Chat(
        title=title,
        user_id=current_user.id,
        status='Pendiente'
    )
    db.session.add(chat)
    db.session.commit()
    
    return jsonify({'success': True, 'chat_id': chat.id})

@chat.route('/<int:chat_id>/accept', methods=['POST'])
@login_required
@requires_admin
def accept_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    
    if chat.status != 'Pendiente':
        return jsonify({'success': False, 'message': 'Este chat ya ha sido aceptado'}), 400
    
    try:
        chat.admin_id = current_user.id
        chat.status = 'Activo'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Chat aceptado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chat.route('/<int:chat_id>/messages', methods=['GET', 'POST'])
@login_required
def chat_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    
    # Verificar que el usuario tenga acceso al chat
    if not (current_user.is_admin or chat.user_id == current_user.id):
        abort(403)
    
    # Si es admin, verificar que sea el asignado al chat
    if current_user.is_admin and chat.status == 'Activo' and chat.admin_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        try:
            # Verificar que el chat esté activo
            if chat.status == 'Cerrado':
                return jsonify({
                    'success': False,
                    'message': 'Este chat está cerrado'
                }), 400
            
            content = request.form.get('content')
            if not content:
                return jsonify({
                    'success': False,
                    'message': 'El contenido del mensaje es requerido'
                }), 400
            
            # Usar el nuevo método add_message
            message = chat.add_message(current_user.id, content)
            
            return jsonify({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'sender_email': message.sender.email,
                    'created_at': message.created_at.strftime('%H:%M')
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    # Marcar mensajes como leídos
    unread_messages = ChatMessage.query.filter_by(
        chat_id=chat_id,
        is_read=False
    ).filter(ChatMessage.sender_id != current_user.id).all()
    
    for message in unread_messages:
        message.mark_as_read()
    
    messages = ChatMessage.query.filter_by(chat_id=chat_id)\
        .order_by(ChatMessage.created_at.asc()).all()
    
    return render_template('chat/messages.html',
                         chat=chat,
                         messages=messages)

@chat.route('/unread/count')
@login_required
def unread_count():
    """JSON endpoint for unread messages count"""
    return jsonify({'count': get_unread_messages_count()})

@chat.route('/pending/count')
@login_required
@requires_admin
def pending_count():
    """JSON endpoint for pending chats count"""
    return jsonify({'count': get_pending_chats_count()})

@chat.route('/active')
@login_required
@requires_admin
def active_chats():
    # Obtener solo los chats activos asignados al admin actual
    chats = Chat.query.filter_by(
        status='Activo',
        admin_id=current_user.id
    ).order_by(Chat.created_at.desc()).all()
    
    return render_template('chat/active_chats.html', chats=chats)

@chat.route('/<int:chat_id>/close', methods=['POST'])
@login_required
@requires_admin
def close_chat(chat_id):
    """Close a chat (admin only)"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Verificar que el admin está asignado a este chat
    if chat.admin_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'No tienes permiso para cerrar este chat'
        }), 403
    
    try:
        chat.close()
        return jsonify({
            'success': True,
            'message': 'Chat cerrado exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
