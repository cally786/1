from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import Equipment, Transaction, Notification
from datetime import datetime

reservation = Blueprint('reservation', __name__)

@reservation.route('/reserve/<int:equipment_id>', methods=['POST'])
@login_required
def reserve_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Verificar que no sea el propietario
    if current_user.id == equipment.creator_id:
        flash('No puedes reservar tu propio equipo', 'warning')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
    
    # Verificar que el equipo esté publicado
    if equipment.status != 'Publicado':
        flash('Este equipo no está disponible para reserva', 'warning')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
    
    try:
        # Obtener y validar la cantidad
        quantity = int(request.form.get('quantity', 1))
        quantity_confirmation = int(request.form.get('quantity_confirmation', 0))
        
        print(f"DEBUG - Cantidad solicitada: {quantity}, Confirmación: {quantity_confirmation}")
        
        # Verificar que las cantidades coincidan
        if quantity != quantity_confirmation:
            print(f"DEBUG - Error: Las cantidades no coinciden")
            flash('Error en la cantidad solicitada', 'danger')
            return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
        
        # Verificar cantidad disponible usando el nuevo método
        can_reserve, message = equipment.check_quantity_status(quantity)
        if not can_reserve:
            print(f"DEBUG - No se puede reservar: {message}")
            flash(message, 'danger')
            return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
        
        # Guardar cantidad anterior para logging
        previous_quantity = equipment.available_quantity
        
        # Crear la transacción
        transaction = Transaction(
            equipment_id=equipment_id,
            buyer_id=current_user.id,
            seller_id=equipment.creator_id,
            quantity=quantity,
            unit_price=equipment.unit_price,
            status='Pendiente'
        )
        
        # Actualizar cantidad disponible
        equipment.available_quantity = max(0, equipment.available_quantity - quantity)
        equipment.update_status_based_on_quantity()
        
        print(f"DEBUG - Reserva: ID={equipment_id}, Anterior={previous_quantity}, Solicitada={quantity}, Nueva={equipment.available_quantity}")
        
        db.session.add(transaction)
        
        # Crear notificación para el vendedor
        seller_notification = Notification(
            recipient_id=equipment.creator_id,
            message=f'Nueva reserva para "{equipment.name}" - Cantidad: {quantity}',
            type='new_reservation',
            equipment_id=equipment_id
        )
        
        db.session.add(seller_notification)
        
        # Verificar si se agotó el stock
        if equipment.available_quantity == 0:
            admin_notification = Notification(
                recipient_id=1,  # ID del admin
                message=f'El equipo "{equipment.name}" se ha agotado',
                type='out_of_stock',
                equipment_id=equipment_id
            )
            db.session.add(admin_notification)
        
        db.session.commit()
        flash('Reserva realizada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar la reserva: {str(e)}', 'danger')
    
    return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
