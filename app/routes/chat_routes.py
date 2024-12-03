from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models.chat import Chat, ChatMessage
from app.utils.decorators import requires_admin
from datetime import datetime
from app.models.models import User

chat = Blueprint('chat', __name__)

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
    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Los administradores no pueden crear chats'}), 403
    
    title = request.form.get('title')
    if not title:
        return jsonify({'success': False, 'message': 'El título es requerido'}), 400
    
    chat = Chat(
        title=title,
        user_id=current_user.id,
        status='Pendiente'
    )
    
    try:
        db.session.add(chat)
        db.session.commit()
        return jsonify({
            'success': True,
            'chat_id': chat.id,
            'message': 'Chat creado exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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
            
            # Si es usuario normal, verificar que el chat esté asignado
            if not current_user.is_admin and chat.status == 'Pendiente':
                return jsonify({
                    'success': False,
                    'message': 'Debes esperar a que un administrador acepte el chat'
                }), 400
            
            content = request.form.get('content')
            if not content:
                return jsonify({
                    'success': False,
                    'message': 'El mensaje no puede estar vacío'
                }), 400
            
            message = ChatMessage(
                chat_id=chat.id,
                sender_id=current_user.id,
                content=content,
                is_read=False
            )
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': current_user.username,
                    'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    # GET request
    messages = ChatMessage.query.filter_by(chat_id=chat.id)\
        .order_by(ChatMessage.created_at.asc()).all()
    
    # Marcar como leídos los mensajes que no son del usuario actual
    unread_messages = ChatMessage.query.filter_by(
        chat_id=chat.id,
        is_read=False
    ).filter(ChatMessage.sender_id != current_user.id).all()
    
    for message in unread_messages:
        message.is_read = True
    
    if unread_messages:
        db.session.commit()
    
    return render_template('chat/messages.html', chat=chat, messages=messages)

@chat.route('/<int:chat_id>/close', methods=['POST'])
@login_required
@requires_admin
def close_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    
    if chat.status == 'Cerrado':
        return jsonify({'success': False, 'message': 'Este chat ya está cerrado'}), 400
    
    if chat.admin_id != current_user.id:
        return jsonify({'success': False, 'message': 'Solo el administrador asignado puede cerrar el chat'}), 403
    
    try:
        chat.status = 'Cerrado'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Chat cerrado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chat.route('/pending/count')
@login_required
def pending_chats_count():
    try:
        if not current_user.is_admin:
            return jsonify({
                'success': True,
                'count': 0
            })
        
        # Contar todos los chats pendientes para admins
        count = Chat.query.filter_by(status='Pendiente').count()
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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

@chat.route('/unread/count')
@login_required
def unread_messages_count():
    try:
        if current_user.is_admin:
            # Para admins, contar mensajes no leídos en chats activos asignados
            unread_count = ChatMessage.query.join(Chat)\
                .filter(Chat.admin_id == current_user.id)\
                .filter(Chat.status == 'Activo')\
                .filter(ChatMessage.is_read == False)\
                .filter(ChatMessage.sender_id != current_user.id)\
                .count()
        else:
            # Para usuarios normales, contar mensajes no leídos en sus chats
            unread_count = ChatMessage.query.join(Chat)\
                .filter(Chat.user_id == current_user.id)\
                .filter(ChatMessage.is_read == False)\
                .filter(ChatMessage.sender_id != current_user.id)\
                .count()
        
        return jsonify({
            'success': True,
            'count': unread_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
