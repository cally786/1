from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/transactions/<int:transaction_id>/cancel', methods=['POST'])
@login_required
def cancel_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Solo permitir cancelar si es admin o si es el comprador/vendedor y la transacción está pendiente
    if not (current_user.is_admin or 
            ((current_user.id == transaction.buyer_id or current_user.id == transaction.seller_id) 
             and transaction.status == 'Pendiente')):
        flash('No tienes permiso para cancelar esta transacción.', 'error')
        return redirect(url_for('transactions'))

    if transaction.status != 'Pendiente':
        flash('Solo se pueden cancelar transacciones pendientes.', 'error')
        return redirect(url_for('transactions'))

    try:
        # Devolver la cantidad al inventario disponible
        equipment = transaction.equipment
        equipment.available_quantity += transaction.quantity
        
        # Actualizar estado de la transacción
        transaction.status = 'Cancelado'
        
        # Crear notificaciones para comprador y vendedor
        if current_user.is_admin:
            buyer_msg = f'Un administrador ha cancelado tu reserva de {transaction.quantity} unidad(es) de {equipment.name}'
            seller_msg = f'Un administrador ha cancelado la reserva de {transaction.quantity} unidad(es) de {equipment.name} por {transaction.buyer.username}'
        else:
            actor = 'comprador' if current_user.id == transaction.buyer_id else 'vendedor'
            buyer_msg = f'El {actor} ha cancelado la reserva de {transaction.quantity} unidad(es) de {equipment.name}'
            seller_msg = buyer_msg

        # Notificar al comprador
        if current_user.id != transaction.buyer_id:
            buyer_notification = Notification(
                recipient_id=transaction.buyer_id,
                message=buyer_msg,
                type='cancellation',
                transaction_id=transaction.id
            )
            db.session.add(buyer_notification)

        # Notificar al vendedor
        if current_user.id != transaction.seller_id:
            seller_notification = Notification(
                recipient_id=transaction.seller_id,
                message=seller_msg,
                type='cancellation',
                transaction_id=transaction.id
            )
            db.session.add(seller_notification)

        db.session.commit()
        flash('Transacción cancelada exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error al cancelar la transacción.', 'error')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('transactions'))
