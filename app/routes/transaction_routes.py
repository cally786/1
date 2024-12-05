# routes/transaction_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.models import Equipment, Transaction, Notification
from app.utils.helpers import requires_admin
from app import db
from datetime import datetime, timedelta

# Cambiar la definición del blueprint
transaction = Blueprint('transaction', __name__, url_prefix='/transaction')

@transaction.route('/equipment/<int:equipment_id>/reserve', methods=['POST'])
@login_required
def reserve_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Verificar que el equipo esté publicado
    if equipment.status != 'Publicado':
        flash('Este equipo no está disponible para reserva.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
    
    # Verificar que haya unidades disponibles
    if equipment.available_quantity <= 0:
        flash('No hay unidades disponibles de este equipo.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
    
    # Verificar que el usuario no sea el creador
    if equipment.creator_id == current_user.id:
        flash('No puedes reservar tu propio equipo.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
    
    # Verificar que no haya una transacción pendiente
    pending_transaction = Transaction.query.filter_by(
        equipment_id=equipment_id,
        buyer_id=current_user.id,
        status='Pendiente'
    ).first()
    
    if pending_transaction:
        flash('Ya tienes una reserva pendiente para este equipo.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
    
    try:
        # Obtener la cantidad del formulario
        quantity = int(request.form.get('quantity', 1))
        
        # Validar la cantidad
        if quantity <= 0:
            flash('La cantidad debe ser mayor a 0.', 'error')
            return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
            
        if quantity > equipment.available_quantity:
            flash(f'Solo hay {equipment.available_quantity} unidades disponibles.', 'error')
            return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
        
        # Crear la transacción
        transaction = Transaction(
            equipment_id=equipment_id,
            buyer_id=current_user.id,
            seller_id=equipment.creator_id,
            quantity=quantity,  # Usar la cantidad del formulario
            unit_price=equipment.unit_price,
            status='Pendiente',
            created_at=datetime.utcnow()
        )
        
        # Crear notificación para el vendedor
        notification = Notification(
            recipient_id=equipment.creator_id,
            message=f'Tienes una nueva solicitud de reserva para "{equipment.name}" - Cantidad: {quantity}',
            type='reservation',
            equipment_id=equipment_id
        )
        
        db.session.add(transaction)
        db.session.add(notification)
        
        # Actualizar la cantidad disponible
        equipment.available_quantity -= quantity
        
        db.session.commit()
        
        flash('Solicitud de reserva enviada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar la reserva: {str(e)}', 'error')
    
    return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))

@transaction.route('/transactions/<int:transaction_id>')
@login_required
def transaction_detail(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if not current_user.is_admin and transaction.buyer_id != current_user.id and transaction.seller_id != current_user.id:
        flash('No tienes permiso para ver esta transacción.', 'error')
        return redirect(url_for('transaction.list_transactions'))
    return render_template('transactions/detail.html', transaction=transaction)

@transaction.route('/transactions/<int:transaction_id>/approve', methods=['POST'])
@login_required
def approve_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el vendedor o un administrador
    if not current_user.is_admin and transaction.seller_id != current_user.id:
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

@transaction.route('/transactions/<int:transaction_id>/reject', methods=['POST'])
@login_required
def reject_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el vendedor o un administrador
    if not current_user.is_admin and transaction.seller_id != current_user.id:
        flash('No tienes permiso para rechazar esta transacción.', 'error')
        return redirect(url_for('transaction.list_transactions'))
    
    if transaction.status != 'Pendiente':
        flash('Esta transacción ya ha sido procesada.', 'error')
        return redirect(url_for('transaction.list_transactions'))
    
    try:
        transaction.status = 'Rechazado'
        transaction.processed_at = datetime.utcnow()
        
        # Actualizar el estado del equipo si es necesario
        equipment = transaction.equipment
        if hasattr(equipment, 'process_transaction_completion'):
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
    
    return redirect(url_for('transaction.list_transactions'))

@transaction.route('/transactions/<int:transaction_id>/cancel', methods=['POST'])
@login_required
def cancel_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el comprador o vendedor
    if transaction.buyer_id != current_user.id and transaction.seller_id != current_user.id:
        flash('No tienes permiso para cancelar esta transacción.', 'error')
        return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
    
    if transaction.status != 'Pendiente':
        flash('Solo se pueden cancelar transacciones pendientes.', 'error')
        return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
    
    try:
        transaction.status = 'Cancelado'
        transaction.processed_at = datetime.utcnow()
        
        # Notificar a la otra parte
        recipient_id = transaction.seller_id if current_user.id == transaction.buyer_id else transaction.buyer_id
        notification = Notification(
            recipient_id=recipient_id,
            message=f'La transacción para "{transaction.equipment.name}" ha sido cancelada.',
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

@transaction.route('/transactions/<int:transaction_id>/complete', methods=['POST'])
@login_required
def complete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verificar que el usuario sea el vendedor o admin
    if not current_user.is_admin and transaction.seller_id != current_user.id:
        flash('No tienes permiso para completar esta transacción.', 'error')
        return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
    
    if transaction.status != 'Aprobado':
        flash('Solo se pueden completar transacciones aprobadas.', 'error')
        return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))
    
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
    
    return redirect(url_for('transaction.transaction_detail', transaction_id=transaction_id))

@transaction.route('/transactions')
@login_required
def list_transactions():
    # Obtener parámetros de filtro
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Iniciar la consulta base
    query = Transaction.query
    
    # Aplicar filtros si están presentes
    if status:
        query = query.filter(Transaction.status == status)
    
    if date_from:
        query = query.filter(Transaction.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(Transaction.created_at <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
    
    # Filtrar por usuario si no es admin
    if not current_user.is_admin:
        query = query.filter(
            (Transaction.buyer_id == current_user.id) |
            (Transaction.seller_id == current_user.id)
        )
    
    # Ordenar por fecha de creación
    transactions = query.order_by(Transaction.created_at.desc()).all()
    
    return render_template('transactions/list.html', transactions=transactions)

@transaction.route('/my-transactions')
@login_required
def my_transactions():
    transactions = Transaction.query.filter(
        (Transaction.buyer_id == current_user.id) |
        (Transaction.seller_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).all()
    return render_template('transactions/my_transactions.html', transactions=transactions)

@transaction.route('/my-sales')
@login_required
def my_sales():
    transactions = Transaction.query\
        .filter_by(seller_id=current_user.id)\
        .order_by(Transaction.created_at.desc())\
        .all()
    return render_template('transactions/my_transactions.html', transactions=transactions)
