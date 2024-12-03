from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import Equipment, Transaction, Notification
from datetime import datetime

transactions_status = Blueprint('transactions_status', __name__)

@transactions_status.route('/transactions/<int:transaction_id>/complete', methods=['POST'])
@login_required
def complete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el vendedor o admin
    if not current_user.is_admin and transaction.seller_id != current_user.id:
        flash('No tienes permiso para completar esta transacción.', 'error')
        return redirect(url_for('transactions.transaction_detail', transaction_id=transaction_id))
    
    if transaction.status != 'Aprobado':
        flash('Solo se pueden completar transacciones aprobadas.', 'error')
        return redirect(url_for('transactions.transaction_detail', transaction_id=transaction_id))
    
    try:
        transaction.status = 'Completado'
        transaction.processed_at = datetime.utcnow()
        
        # Actualizar el estado del equipo
        equipment = transaction.equipment
        equipment.process_transaction_completion(transaction)
        
        # Notificar al comprador
        notification = Notification(
            recipient_id=transaction.buyer_id,
            message=f'La transacción para "{transaction.equipment.name}" ha sido completada.',
            type='transaction_completed',
            equipment_id=transaction.equipment_id
        )
        
        db.session.add(notification)
        db.session.commit()
        flash('Transacción completada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al completar la transacción: {str(e)}', 'error')
    
    return redirect(url_for('transactions.transaction_detail', transaction_id=transaction_id))

@transactions_status.route('/transactions/<int:transaction_id>/reject', methods=['POST'])
@login_required
def reject_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el vendedor o admin
    if not current_user.is_admin and transaction.seller_id != current_user.id:
        flash('No tienes permiso para rechazar esta transacción.', 'error')
        return redirect(url_for('transactions.transaction_detail', transaction_id=transaction_id))
    
    if transaction.status != 'Pendiente':
        flash('Esta transacción ya ha sido procesada.', 'error')
        return redirect(url_for('transactions.transaction_detail', transaction_id=transaction_id))
    
    try:
        transaction.status = 'Rechazado'
        transaction.processed_at = datetime.utcnow()
        
        # Actualizar el estado del equipo
        equipment = transaction.equipment
        equipment.process_transaction_completion(transaction)
        
        # Notificar al comprador
        notification = Notification(
            recipient_id=transaction.buyer_id,
            message=f'Tu reserva para "{transaction.equipment.name}" ha sido rechazada.',
            type='transaction_rejected',
            equipment_id=transaction.equipment_id
        )
        
        db.session.add(notification)
        db.session.commit()
        flash('Transacción rechazada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al rechazar la transacción: {str(e)}', 'error')
    
    return redirect(url_for('transactions.transaction_detail', transaction_id=transaction_id))

@transactions_status.route('/transactions/<int:transaction_id>/update-status', methods=['POST'])
@login_required
def update_status(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el vendedor o admin
    if not current_user.is_admin and transaction.seller_id != current_user.id:
        return jsonify({'success': False, 'error': 'No tienes permiso para actualizar esta transacción.'})
    
    # Obtener el nuevo estado
    try:
        if request.is_json:
            data = request.get_json()
            new_status = data.get('status')
        else:
            new_status = request.form.get('status')
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error al procesar la solicitud: {str(e)}'})

    if not new_status:
        return jsonify({'success': False, 'error': 'No se proporcionó un nuevo estado'})
    
    valid_statuses = ['Pendiente', 'Aprobado', 'Rechazado', 'Completado']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Estado inválido'})
    
    try:
        transaction.status = new_status
        transaction.processed_at = datetime.utcnow()
        
        if new_status in ['Completado', 'Rechazado']:
            # Actualizar el estado del equipo
            equipment = transaction.equipment
            equipment.process_transaction_completion(transaction)
        
        # Notificar al comprador
        message = {
            'Aprobado': 'Tu reserva ha sido aprobada.',
            'Rechazado': 'Tu reserva ha sido rechazada.',
            'Completado': 'Tu reserva ha sido completada.'
        }.get(new_status)
        
        if message:
            notification = Notification(
                recipient_id=transaction.buyer_id,
                message=f'{message} - {transaction.equipment.name}',
                type=f'transaction_{new_status.lower()}',
                equipment_id=transaction.equipment_id
            )
            db.session.add(notification)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estado de la transacción actualizado exitosamente.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error al actualizar la transacción: {str(e)}'})
