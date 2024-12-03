from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.models.models import Equipment, Category
from app.utils.helpers import allowed_file

equipment_creation = Blueprint('equipment_creation', __name__)

@equipment_creation.route('/add_equipment', methods=['GET', 'POST'])
@login_required
def add_equipment():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.form.get('name')
            description = request.form.get('description')
            quantity = request.form.get('quantity')
            category_id = request.form.get('category_id')
            
            if not category_id:
                return jsonify({
                    'success': False,
                    'message': 'Por favor seleccione una categoría'
                })

            category = Category.query.get(category_id)
            if not category:
                return jsonify({
                    'success': False,
                    'message': 'La categoría seleccionada no existe'
                })

            company = request.form.get('company')
            model = request.form.get('model')
            serial_number = request.form.get('serial_number')
            unit_price = request.form.get('unit_price')
            notes = request.form.get('notes')
            location = request.form.get('location')

            # Validar campos requeridos
            if not all([name, quantity, category_id]):
                return jsonify({
                    'success': False,
                    'message': 'Por favor complete todos los campos requeridos.'
                })

            try:
                quantity = int(quantity)
                unit_price = float(unit_price) if unit_price else 0.0
                category_id = int(category_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'La cantidad y el precio deben ser números válidos.'
                })

            # Verificar si ya existe un equipo con el mismo número de serie
            if serial_number:
                existing_equipment = Equipment.query.filter_by(serial_number=serial_number).first()
                if existing_equipment:
                    return jsonify({
                        'success': False,
                        'message': 'Ya existe un equipo con ese número de serie.'
                    })

            # Crear nuevo equipo
            equipment = Equipment(
                name=name,
                description=description,
                quantity=quantity,
                available_quantity=quantity,
                category_id=category_id,
                creator_id=current_user.id,
                company=company,
                model=model,
                serial_number=serial_number,
                unit_price=unit_price,
                notes=notes,
                location=location,
                status='En revisión'  # Estado inicial
            )

            # Procesar la imagen si se proporcionó una
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    equipment.image_filename = filename

            db.session.add(equipment)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Equipo agregado exitosamente.',
                'redirect': url_for('equipment.my_equipment')
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error al agregar el equipo: {str(e)}'
            })

    # GET request - mostrar formulario
    return render_template('add_equipment.html', categories=categories)
