# routes/notification_routes.py

from flask import Blueprint, jsonify, request, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import Notification

notification = Blueprint('notification', __name__)

@notification.route('/notifications')
@login_required
def notifications():
    try:
        unread_notifications = Notification.query.filter_by(
            recipient_id=current_user.id,
            read=False
        ).order_by(Notification.created_at.desc()).all()

        read_notifications = Notification.query.filter_by(
            recipient_id=current_user.id,
            read=True
        ).order_by(Notification.created_at.desc()).limit(50).all()

        return render_template('notifications.html',
                             unread_notifications=unread_notifications,
                             read_notifications=read_notifications)
    except Exception as e:
        flash('Error al cargar las notificaciones: ' + str(e), 'error')
        return redirect(url_for('main.index'))

@notification.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.recipient_id != current_user.id:
        abort(403)
    
    notification.read = True
    db.session.commit()
    return redirect(url_for('notification.notifications'))

@notification.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    try:
        notification_ids = request.json.get('notification_ids', [])
        notifications = Notification.query.filter(
            Notification.id.in_(notification_ids),
            Notification.recipient_id == current_user.id
        ).all()
        
        for notification in notifications:
            notification.read = True
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@notification.route('/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    try:
        count = Notification.query.filter_by(
            recipient_id=current_user.id,
            read=False
        ).count()
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification.route('/notifications/unread', methods=['GET'])
@login_required
def get_unread_notifications():
    try:
        unread_notifications = Notification.query.filter_by(
            recipient_id=current_user.id,
            read=False
        ).order_by(Notification.created_at.desc()).all()
        
        notifications_data = [{
            'id': notification.id,
            'message': notification.message,
            'type': notification.type,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M')
        } for notification in unread_notifications]
        
        return jsonify({
            'success': True,
            'notifications': notifications_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@notification.route('/notifications/mark-shown-as-read', methods=['POST'])
@login_required
def mark_shown_notifications_read():
    try:
        notification_ids = request.json.get('notification_ids', [])
        if not notification_ids:
            return jsonify({'success': False, 'error': 'No notification IDs provided'}), 400

        notifications = Notification.query.filter(
            Notification.id.in_(notification_ids),
            Notification.recipient_id == current_user.id
        ).all()

        for notification in notifications:
            notification.read = True

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
