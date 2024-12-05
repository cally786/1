from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/add-equipment', methods=['GET', 'POST'])
@login_required
def add_equipment():
    if request.method == 'POST':
        try:
            # Validar que todos los campos requeridos estén presentes
            required_fields = ['company', 'name', 'model', 'category', 'serial_number', 'quantity', 'unit_price', 'location']
            for field in required_fields:
                if field not in request.form or not request.form[field]:
                    raise ValueError(f'El campo {field} es requerido.')

            # Validar tipos de datos
            try:
                quantity = int(request.form['quantity'])
                if quantity < 0:
                    raise ValueError('La cantidad debe ser un número positivo.')
            except ValueError:
                raise ValueError('La cantidad debe ser un número válido.')

            try:
                unit_price = float(request.form['unit_price'])
                if unit_price < 0:
                    raise ValueError('El precio unitario debe ser un número positivo.')
            except ValueError:
                raise ValueError('El precio unitario debe ser un número válido.')

            # Verificar si ya existe un equipo con la misma categoría y número de serie
            existing_equipment = Equipment.query.filter_by(
                category=request.form['category'],
                serial_number=request.form['serial_number']
            ).first()
            
            if existing_equipment:
                raise ValueError('Ya existe un equipo con la misma categoría y número de serie.')
            
            # Crear nuevo equipo
            equipment = Equipment(
                company=request.form['company'],
                name=request.form['name'],
                model=request.form['model'],
                category=request.form['category'],
                serial_number=request.form['serial_number'],
                quantity=quantity,
                unit_price=unit_price,
                location=request.form['location'],
                notes=request.form.get('notes', ''),
                creator_id=current_user.id
            )
            
            # Manejar el estado según el rol del usuario
            if current_user.is_admin:
                equipment.status = request.form.get('status', 'En revisión')
                if equipment.status == 'Publicado':
                    equipment.published_at = datetime.utcnow()
            else:
                equipment.status = 'En revisión'
            
            # Manejar la imagen si se proporciona
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    equipment.image_filename = filename
            
            db.session.add(equipment)
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Equipo agregado exitosamente',
                    'redirect': url_for('index')
                })
            
            flash('Equipo agregado exitosamente', 'success')
            return redirect(url_for('index'))
            
        except ValueError as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': str(e)
                })
            flash(str(e), 'danger')
            return render_template('add_equipment.html')
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': f'Error inesperado: {str(e)}'
                })
            flash(f'Error inesperado: {str(e)}', 'danger')
            return render_template('add_equipment.html')
    
    return render_template('add_equipment.html')
