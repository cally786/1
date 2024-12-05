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
        elif field == 'category':
            category_ids = [cat.id for cat in Category.query.filter(Category.name.in_(values)).all()]
            query = query.filter(Equipment.category_id.in_(category_ids))
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
    if request.method == 'POST':
        try:
            # Verificar campos requeridos
            required_fields = ['name', 'company', 'model', 'category', 'serial_number', 'quantity', 'unit_price', 'location']
            for field in required_fields:
                if field not in request.form or not request.form[field].strip():
                    raise ValueError(f'El campo {field} es requerido')

            # Validar tipos de datos
            try:
                quantity = int(request.form['quantity'])
                if quantity < 0:
                    raise ValueError('La cantidad debe ser un número positivo')
            except ValueError:
                raise ValueError('La cantidad debe ser un número válido')

            try:
                unit_price = float(request.form['unit_price'])
                if unit_price < 0:
                    raise ValueError('El precio debe ser un número positivo')
            except ValueError:
                raise ValueError('El precio debe ser un número válido')

            # Verificar si ya existe un equipo con el mismo número de serie
            if request.form['serial_number']:
                existing_equipment = Equipment.query.filter_by(
                    serial_number=request.form['serial_number']
                ).first()
                if existing_equipment:
                    raise ValueError('Ya existe un equipo con ese número de serie')

            # Obtener o crear la categoría
            category_name = request.form['category']
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
                db.session.flush()  # Para obtener el ID de la categoría

            # Crear nuevo equipo
            equipment = Equipment(
                name=request.form['name'],
                company=request.form['company'],
                model=request.form['model'],
                category_id=category.id,  # Usar el ID de la categoría
                serial_number=request.form['serial_number'],
                quantity=quantity,
                available_quantity=quantity,
                unit_price=unit_price,
                location=request.form['location'],
                notes=request.form.get('notes', ''),
                creator_id=current_user.id,
                status='En revisión'
            )

            # Procesar la imagen si se proporcionó una
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    equipment.image_filename = filename

            db.session.add(equipment)
            db.session.commit()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Equipo agregado exitosamente',
                    'redirect': url_for('equipment.my_equipment')
                })
            
            flash('Equipo agregado exitosamente', 'success')
            return redirect(url_for('equipment.my_equipment'))

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

    # GET request
    categories = Category.query.order_by(Category.name).all()
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
    elif field == 'category':
        # Get distinct category names
        if current_user.is_admin:
            query_result = db.session.query(Category.name.distinct()).join(Equipment).all()
        else:
            query_result = db.session.query(Category.name.distinct()).join(Equipment).filter(Equipment.creator_id == current_user.id).all()
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
def rejected_equipment():
    if not current_user.is_admin:
        abort(403)
    equipment_list = Equipment.query.filter_by(status='Rechazado').order_by(Equipment.created_at.desc()).all()
    rejected_count = len(equipment_list)
    stats = {'total': rejected_count, 'pending': 0, 'reviewed': 0, 'published': 0, 'rejected': rejected_count}
    return render_template('index.html', equipment_list=equipment_list, stats=stats, title='Equipos Rechazados')

@equipment.route('/my-equipment')
@login_required
def my_equipment():
    equipment_list = Equipment.query.filter_by(creator_id=current_user.id).all()
    
    # Calcular estadísticas
    stats = {
        'total_equipment': Equipment.query.filter_by(creator_id=current_user.id).count(),
        'status_counts': {
            'En revisión': Equipment.query.filter_by(creator_id=current_user.id, status='En revisión').count(),
            'Revisado': Equipment.query.filter_by(creator_id=current_user.id, status='Revisado').count(),
            'Publicado': Equipment.query.filter_by(creator_id=current_user.id, status='Publicado').count(),
            'Rechazado': Equipment.query.filter_by(creator_id=current_user.id, status='Rechazado').count(),
            'Agotado': Equipment.query.filter_by(creator_id=current_user.id, status='Agotado').count()
        }
    }
    
    return render_template('equipment/my_equipment.html',
                         equipment_list=equipment_list,
                         stats=stats,
                         show_actions=True,
                         title='Mis Equipos')

@equipment.route('/get_equipment_list')
@login_required
def get_equipment_list():
    status = request.args.get('status')
    query = Equipment.query

    if status:
        query = query.filter_by(status=status)

    # Aplicar filtros basados en el rol del usuario
    if not current_user.is_admin:
        query = query.filter(
            db.or_(
                Equipment.creator_id == current_user.id,
                db.and_(
                    Equipment.creator_id != current_user.id,
                    Equipment.status == 'Publicado'
                )
            )
        )

    equipment_list = query.order_by(Equipment.created_at.desc()).all()
    
    return render_template('equipment/_equipment_list.html', 
                         equipment_list=equipment_list,
                         show_actions=True)
