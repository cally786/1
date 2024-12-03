from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/equipment/<int:equipment_id>/reserve', methods=['POST'])
@login_required
def reserve_equipment(equipment_id):
    if current_user.is_admin:
        flash('Los administradores no pueden realizar reservas.', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))

    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Verificar si el usuario es el propietario
    if equipment.creator_id == current_user.id:
        flash('No puedes reservar tu propio equipo.', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))

    # Verificar si hay suficiente cantidad disponible
    quantity = int(request.form.get('quantity', 1))
    if quantity <= 0:
        flash('La cantidad debe ser mayor que 0.', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))
    
    if quantity > equipment.available_quantity:
        flash('No hay suficiente cantidad disponible.', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))

    # Crear la transacción
    transaction = Transaction(
        equipment_id=equipment.id,
        buyer_id=current_user.id,
        seller_id=equipment.creator_id,
        quantity=quantity,
        unit_price=equipment.unit_price,
        status='Pendiente'
    )

    # Actualizar la cantidad disponible
    equipment.available_quantity -= quantity

    # Crear notificación para el vendedor
    notification = Notification(
        recipient_id=equipment.creator_id,
        message=f'Nueva solicitud de reserva para {equipment.name} por {current_user.username}',
        type='reservation',
        transaction_id=transaction.id
    )

    try:
        db.session.add(transaction)
        db.session.add(notification)
        db.session.commit()
        flash('Solicitud de reserva enviada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar la reserva.', 'error')
        print(f"Error: {str(e)}")

    return redirect(url_for('equipment_detail', equipment_id=equipment_id))
