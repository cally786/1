from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/equipment/<int:equipment_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_admin
def edit_equipment(equipment_id):
    equipment = db.session.get(Equipment, equipment_id)
    if not equipment:
        flash('Equipo no encontrado.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Obtener la cantidad anterior y la nueva
            old_quantity = equipment.quantity
            new_quantity = int(request.form.get('quantity', 0))
            
            # Calcular la diferencia
            quantity_difference = new_quantity - old_quantity
            
            # Actualizar los datos del equipo
            equipment.name = request.form.get('name')
            equipment.company = request.form.get('company')
            equipment.model = request.form.get('model')
            equipment.category = request.form.get('category')
            equipment.serial_number = request.form.get('serial_number')
            equipment.quantity = new_quantity
            equipment.unit_price = float(request.form.get('unit_price', 0))
            equipment.location = request.form.get('location')
            equipment.notes = request.form.get('notes', '')
            
            # Actualizar la cantidad disponible sumando la diferencia
            if equipment.available_quantity is None:
                equipment.available_quantity = new_quantity
            else:
                equipment.available_quantity = max(0, equipment.available_quantity + quantity_difference)
            
            # Actualizar el estado basado en la cantidad disponible
            if equipment.available_quantity == 0 and equipment.status == 'Publicado':
                equipment.status = 'Acabado'
                # Notificar al vendedor
                notification = Notification(
                    recipient_id=equipment.creator_id,
                    message=f'Tu producto "{equipment.name}" se ha marcado como agotado.',
                    type='stock_empty'
                )
                db.session.add(notification)
            elif equipment.available_quantity > 0 and equipment.status == 'Acabado':
                equipment.status = 'Publicado'
                # Notificar al vendedor
                notification = Notification(
                    recipient_id=equipment.creator_id,
                    message=f'Tu producto "{equipment.name}" está nuevamente disponible con {equipment.available_quantity} unidades.',
                    type='stock_available'
                )
                db.session.add(notification)
            
            # Manejar el estado si se cambia manualmente
            if 'status' in request.form:
                new_status = request.form['status']
                if new_status != equipment.status:
                    equipment.status = new_status
                    if new_status == 'Publicado':
                        equipment.published_at = datetime.utcnow()
            
            # Manejar la imagen si se proporciona una nueva
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    if equipment.image_filename:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], equipment.image_filename))
                        except:
                            pass
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    equipment.image_filename = filename

            db.session.commit()
            flash('Equipo actualizado exitosamente.', 'success')
            return redirect(url_for('equipment_detail', equipment_id=equipment.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el equipo. Por favor, intente de nuevo.', 'danger')
            print(f"Error: {str(e)}")
            return render_template('edit_equipment.html', equipment=equipment)
    
    return render_template('edit_equipment.html', equipment=equipment)
