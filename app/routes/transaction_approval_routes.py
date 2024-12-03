from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.models import Transaction, Notification
from app import db
from datetime import datetime

transaction_approval = Blueprint('transaction_approval', __name__)

@transaction_approval.route('/transactions/<int:transaction_id>/approve', methods=['POST'])
@login_required
def approve_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el vendedor
    if transaction.seller_id != current_user.id:
        flash('No tienes permiso para aprobar esta transacción.', 'error')
        return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
    
    if transaction.status != 'Pendiente':
        flash('Esta transacción ya ha sido procesada.', 'error')
        return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
    
    try:
        transaction.status = 'Aprobado'
        transaction.processed_at = datetime.utcnow()
        
        # Notificar al comprador
        notification = Notification(
            recipient_id=transaction.buyer_id,
            message=f'Tu reserva para "{transaction.equipment.name}" ha sido aprobada.',
            type='transaction_approved',
            equipment_id=transaction.equipment_id
        )
        
        db.session.add(notification)
        db.session.commit()
        flash('Transacción aprobada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al aprobar la transacción: {str(e)}', 'error')
    
    return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))

@transaction_approval.route('/transactions/<int:transaction_id>/cancel', methods=['POST'])
@login_required
def cancel_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el comprador
    if transaction.buyer_id != current_user.id:
        flash('No tienes permiso para cancelar esta transacción.', 'error')
        return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
    
    if transaction.status != 'Pendiente':
        flash('Solo se pueden cancelar transacciones pendientes.', 'error')
        return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
    
    try:
        transaction.status = 'Cancelado'
        transaction.processed_at = datetime.utcnow()
        
        # Notificar al vendedor
        notification = Notification(
            recipient_id=transaction.seller_id,
            message=f'La reserva para "{transaction.equipment.name}" ha sido cancelada por el comprador.',
            type='transaction_cancelled',
            equipment_id=transaction.equipment_id
        )
        
        db.session.add(notification)
        db.session.commit()
        flash('Transacción cancelada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cancelar la transacción: {str(e)}', 'error')
    
    return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
