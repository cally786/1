from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.models import Equipment
from app.services.price_negotiation_service import (
    get_pending_negotiation,
    handle_price_acceptance,
    handle_price_rejection,
    can_modify_equipment
)

price_negotiation = Blueprint('price_negotiation', __name__)

@price_negotiation.route('/api/equipment/<int:equipment_id>/price/response', methods=['POST'])
@login_required
def respond_to_price_change(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Verificar que el usuario sea el creador del equipo
    if not can_modify_equipment(equipment, current_user.id):
        return jsonify({'error': 'No autorizado'}), 403
    
    # Verificar que el equipo esté en estado Pre-Publicado
    if equipment.status != 'Pre-Publicado':
        return jsonify({'error': 'El equipo no está en proceso de negociación'}), 400
    
    data = request.get_json()
    accepted = data.get('accepted', False)
    
    if accepted:
        success, message = handle_price_acceptance(equipment_id, current_user.id)
    else:
        rejection_reason = data.get('rejection_reason')
        if not rejection_reason:
            return jsonify({'error': 'Se requiere un motivo para el rechazo'}), 400
        success, message = handle_price_rejection(equipment_id, current_user.id, rejection_reason)
    
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'new_status': equipment.status
        })
    return jsonify({'error': message}), 400

@price_negotiation.route('/equipment/<int:equipment_id>/price-change', methods=['GET'])
@login_required
def price_change_form(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Verificar que el usuario sea el creador del equipo
    if not can_modify_equipment(equipment, current_user.id):
        flash('No autorizado', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))
    
    # Verificar que el equipo esté en estado Pre-Publicado
    if equipment.status != 'Pre-Publicado':
        flash('El equipo no está en proceso de negociación', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))
    
    negotiation = get_pending_negotiation(equipment_id)
    if not negotiation:
        flash('No se encontró una negociación pendiente', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))
    
    return render_template(
        'price_negotiation.html',
        equipment=equipment,
        negotiation=negotiation
    )
