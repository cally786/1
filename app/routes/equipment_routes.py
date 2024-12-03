# routes/equipment_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from app import db
from app.models.models import Equipment, Notification, User, Transaction, Category
from app.utils.helpers import allowed_file, requires_admin

equipment = Blueprint('equipment', __name__)

@equipment.route('/all_equipment')
@login_required
def all_equipment():
    query = Equipment.query

    # Get filter parameters (now supporting multiple values)
    filters = {}
    for field in ['name', 'company', 'location', 'category', 'creator', 'status']:
        values = request.args.getlist(field)
        if values and values[0]:  # Check if there are any non-empty values
            filters[field] = values

    # Apply filters
    for field, values in filters.items():
        if field == 'creator':
            creator_ids = [user.id for user in User.query.filter(User.username.in_(values)).all()]
            query = query.filter(Equipment.creator_id.in_(creator_ids))
        else:
            query = query.filter(getattr(Equipment, field).in_(values))

    # Get equipment list based on user role
    if current_user.is_admin:
        # Los administradores ven todos los equipos
        equipment_list = query.order_by(Equipment.created_at.desc()).all()
    else:
        # Los usuarios normales ven:
        # 1. Sus propios productos en cualquier estado
        # 2. Productos publicados de otros usuarios
        query = query.filter(
            db.or_(
                Equipment.creator_id == current_user.id,  # Sus propios productos
                db.and_(  # Productos publicados de otros
                    Equipment.creator_id != current_user.id,
                    Equipment.status == 'Publicado'
                )
            )
        )
        equipment_list = query.order_by(Equipment.created_at.desc()).all()

    return render_template('all_equipment.html', equipment_list=equipment_list)

@equipment.route('/add_equipment', methods=['GET', 'POST'])
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
                flash('Por favor seleccione una categoría', 'error')
                return redirect(url_for('equipment.add_equipment'))

            category = Category.query.get(category_id)
            if not category:
                flash('La categoría seleccionada no existe', 'error')
                return redirect(url_for('equipment.add_equipment'))

            company = request.form.get('company')
            model = request.form.get('model')
            serial_number = request.form.get('serial_number')
            unit_price = request.form.get('unit_price')
            notes = request.form.get('notes')
            location = request.form.get('location')

            # Validar campos requeridos
            if not all([name, quantity, category_id]):
                flash('Por favor complete todos los campos requeridos.', 'danger')
                return redirect(url_for('equipment.add_equipment'))

            try:
                quantity = int(quantity)
                unit_price = float(unit_price) if unit_price else 0.0
                category_id = int(category_id)  # Convertir el ID a entero
            except ValueError:
                flash('La cantidad y el precio deben ser números válidos.', 'danger')
                return redirect(url_for('equipment.add_equipment'))

            # Verificar si ya existe un equipo con el mismo número de serie
            if serial_number:
                existing_equipment = Equipment.query.filter_by(serial_number=serial_number).first()
                if existing_equipment:
                    flash('Ya existe un equipo con ese número de serie.', 'danger')
                    return redirect(url_for('equipment.add_equipment'))

            # Crear nuevo equipo
            equipment = Equipment(
                name=name,
                description=description,
                quantity=quantity,
                available_quantity=quantity,
                category_id=category_id,  # Asignar el ID de la categoría
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
            flash('Equipo agregado exitosamente.', 'success')
            return redirect(url_for('equipment.my_equipment'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar el equipo: {str(e)}', 'danger')
            return redirect(url_for('equipment.add_equipment'))

    # GET request - mostrar formulario
    return render_template('add_equipment.html', categories=categories)

@equipment.route('/equipment/<int:equipment_id>')
@login_required
def equipment_detail(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template('equipment_detail.html', equipment=equipment)

@equipment.route('/edit-equipment/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    categories = Category.query.order_by(Category.name).all()
    
    # Verificar permisos
    if not current_user.is_admin and equipment.creator_id != current_user.id:
        abort(403)
    
    # Si el equipo está en estado Pre-Publicado, no se puede editar
    if equipment.status == 'Pre-Publicado':
        flash('No se puede editar el equipo mientras está en proceso de negociación.', 'warning')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
    
    if request.method == 'POST':
        try:
            # Actualizar campos básicos
            equipment.name = request.form['name']
            equipment.company = request.form['company']
            equipment.model = request.form['model']
            
            # Verificar y actualizar la categoría
            category_id = request.form.get('category_id')
            if category_id:
                category = Category.query.get(category_id)
                if category:
                    equipment.category_id = category_id
                else:
                    flash('La categoría seleccionada no es válida.', 'danger')
                    return render_template('edit_equipment.html', equipment=equipment, categories=categories)
            
            equipment.serial_number = request.form['serial_number']
            equipment.quantity = int(request.form['quantity'])
            equipment.location = request.form['location']
            equipment.notes = request.form.get('notes', '')
            
            # Si es admin, manejar cambio de estado
            if current_user.is_admin:
                new_status = request.form.get('status', 'En revisión')
                if new_status != equipment.status:
                    equipment.status = new_status
                    
                    # Notificar al creador sobre el cambio de estado
                    notification = Notification(
                        recipient_id=equipment.creator_id,
                        message=f'Tu producto "{equipment.name}" ha cambiado a estado {new_status}.',
                        type='status_change',
                        equipment_id=equipment_id
                    )
                    db.session.add(notification)
            
            # Si no es admin, actualizar precio
            if not current_user.is_admin:
                equipment.unit_price = float(request.form['unit_price'])
            
            # Manejar la imagen
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    if equipment.image_filename:
                        try:
                            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], equipment.image_filename))
                        except Exception as e:
                            current_app.logger.error(f"Error removing old image: {str(e)}")
                    
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    equipment.image_filename = filename

            # Guardar cambios
            db.session.commit()
            flash('Equipo actualizado exitosamente.', 'success')
            return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el equipo: {str(e)}', 'danger')
            return render_template('edit_equipment.html', equipment=equipment, categories=categories)

    # GET request
    return render_template('edit_equipment.html', equipment=equipment, categories=categories)

@equipment.route('/equipment/<int:equipment_id>/delete')
@login_required
def delete_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Verificar si el usuario tiene permiso para eliminar
    if not current_user.is_admin and equipment.creator_id != current_user.id:
        flash('No tienes permiso para eliminar este equipo.', 'danger')
        return redirect(url_for('equipment.all_equipment'))
    
    # Eliminar la imagen si existe
    if equipment.image_filename:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], equipment.image_filename))
        except:
            pass
    
    db.session.delete(equipment)
    db.session.commit()
    flash('Equipo eliminado exitosamente.', 'success')
    return redirect(url_for('equipment.all_equipment'))

@equipment.route('/get-suggestions')
@login_required
def get_suggestions():
    field = request.args.get('field')
    query = request.args.get('q', '')
    
    if not field or not query:
        return jsonify([])
    
    # Mapeo de campos a columnas de la base de datos
    field_map = {
        'name': Equipment.name,
        'company': Equipment.company,
        'location': Equipment.location,
        'category': Equipment.category,
        'model': Equipment.model,
        'serial_number': Equipment.serial_number
    }
    
    if field not in field_map:
        return jsonify([])
    
    # Realizar la búsqueda
    results = db.session.query(field_map[field])\
        .filter(field_map[field].ilike(f'%{query}%'))\
        .distinct()\
        .limit(10)\
        .all()
    
    # Extraer los valores únicos
    suggestions = [row[0] for row in results if row[0]]
    
    return jsonify(suggestions)

@equipment.route('/get_distinct_values')
@login_required
def get_distinct_values():
    field = request.args.get('field')
    if not field:
        return jsonify({'error': 'Field parameter is required'}), 400

    valid_fields = ['name', 'company', 'location', 'category', 'creator']
    if field not in valid_fields:
        return jsonify({'error': 'Invalid field'}), 400

    query_result = None
    if field == 'creator':
        # Get distinct usernames for creators
        if current_user.is_admin:
            query_result = db.session.query(User.username.distinct()).all()
        else:
            query_result = db.session.query(User.username.distinct()).filter(User.id == current_user.id).all()
    else:
        # Get distinct values for other fields
        if current_user.is_admin:
            query_result = db.session.query(getattr(Equipment, field).distinct()).all()
        else:
            query_result = db.session.query(getattr(Equipment, field).distinct()).filter_by(creator_id=current_user.id).all()

    values = [value[0] for value in query_result if value[0]]  # Filter out None values
    return jsonify({'values': sorted(values)})

@equipment.route('/in-review')
@login_required
@requires_admin
def in_review_equipment():
    equipment_list = Equipment.query.filter_by(status='En revisión').all()
    return render_template('index.html', 
                         equipment_list=equipment_list,
                         status_colors={'En revisión': 'warning'})

@equipment.route('/reviewed')
@login_required
@requires_admin
def reviewed_equipment():
    equipment_list = Equipment.query.filter_by(status='Revisado').all()
    return render_template('index.html', 
                         equipment_list=equipment_list,
                         status_colors={'Revisado': 'info'})

@equipment.route('/rejected')
@login_required
@requires_admin
def rejected_equipment():
    # Get only rejected equipment
    equipment_list = Equipment.query.filter_by(status='Rechazado').order_by(Equipment.created_at.desc()).all()
    
    # For rejected view, only show the count of rejected items
    rejected_count = len(equipment_list)
    stats = {
        'total': rejected_count,  # Total is the same as rejected count
        'pending': 0,  # Hide other stats
        'reviewed': 0,
        'published': 0,
        'rejected': rejected_count  # Add rejected count
    }
    
    return render_template('index.html', 
                         equipment_list=equipment_list,
                         stats=stats,
                         title='Equipos Rechazados')

@equipment.route('/published')
@login_required
def published_equipment():
    filter_status = request.args.get('filter_status', 'Publicado')
    
    # Si el usuario es admin, puede ver todos los equipos
    if current_user.is_admin:
        if filter_status == 'all':
            equipment_list = Equipment.query.all()
        else:
            equipment_list = Equipment.query.filter_by(status=filter_status).all()
    else:
        # Si no es admin, solo ve los equipos publicados
        equipment_list = Equipment.query.filter_by(status='Publicado').all()
    
    # Calcular estadísticas
    total_equipment = Equipment.query.count()
    published_equipment = Equipment.query.filter_by(status='Publicado').count()
    in_review_equipment = Equipment.query.filter_by(status='En revisión').count()
    reviewed_equipment = Equipment.query.filter_by(status='Revisado').count()
    borrowed_equipment = Equipment.query.filter(
        Equipment.available_quantity < Equipment.quantity
    ).count()
    pending_transactions = Transaction.query.filter_by(status='Pendiente').count()
    
    stats = {
        'total_equipment': total_equipment,
        'published_equipment': published_equipment,
        'in_review_equipment': in_review_equipment,
        'reviewed_equipment': reviewed_equipment,
        'borrowed_equipment': borrowed_equipment,
        'pending_transactions': pending_transactions
    }
    
    status_colors = {
        'En revisión': 'warning',
        'Revisado': 'info',
        'Publicado': 'success',
        'Rechazado': 'danger'
    }
    
    title = 'Todos los Equipos' if filter_status == 'all' else f'Equipos {filter_status}'
    
    return render_template('index.html', 
                         equipment_list=equipment_list,
                         stats=stats,
                         status_colors=status_colors,
                         title=title)

@equipment.route('/my-equipment')
@login_required
def my_equipment():
    equipment_list = Equipment.query.filter_by(creator_id=current_user.id).all()
    
    # Calcular estadísticas
    total_equipment = Equipment.query.filter_by(creator_id=current_user.id).count()
    available_equipment = Equipment.query.filter_by(
        creator_id=current_user.id,
        status='Publicado'
    ).count()
    borrowed_equipment = Equipment.query.filter(
        Equipment.creator_id == current_user.id,
        Equipment.available_quantity < Equipment.quantity
    ).count()
    pending_transactions = Transaction.query.filter(
        (Transaction.seller_id == current_user.id) &
        (Transaction.status == 'Pendiente')
    ).count()
    
    stats = {
        'total_equipment': total_equipment,
        'available_equipment': available_equipment,
        'borrowed_equipment': borrowed_equipment,
        'pending_transactions': pending_transactions
    }
    
    return render_template('index.html',
                         equipment_list=equipment_list,
                         stats=stats,
                         title='Mis Equipos')
