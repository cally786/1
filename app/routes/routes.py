from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from app import app, db
from app.models.models import *
from app.utils.utils import *

@app.route('/')
@login_required
def index():
    if current_user.is_admin:
        equipment_list = Equipment.query.filter(Equipment.status != 'Rechazado').order_by(Equipment.created_at.desc()).all()
        total = Equipment.query.filter(Equipment.status != 'Rechazado').count()
        pending = Equipment.query.filter_by(status='En revisión').count()
        reviewed = Equipment.query.filter_by(status='Revisado').count()
        published = Equipment.query.filter_by(status='Publicado').count()
        stats = {'total': total, 'pending': pending, 'reviewed': reviewed, 'published': published}
    else:
        equipment_list = Equipment.query.filter_by(creator_id=current_user.id).order_by(Equipment.created_at.desc()).all()
        total = Equipment.query.filter_by(creator_id=current_user.id).count()
        pending = Equipment.query.filter_by(creator_id=current_user.id, status='En revisión').count()
        reviewed = Equipment.query.filter_by(creator_id=current_user.id, status='Revisado').count()
        published = Equipment.query.filter_by(creator_id=current_user.id, status='Publicado').count()
        stats = {'total': total, 'pending': pending, 'reviewed': reviewed, 'published': published}
    return render_template('index.html', equipment_list=equipment_list, stats=stats, title='Panel de Control')

@app.route('/all-equipment')
@login_required
def all_equipment_redirect():
    return redirect(url_for('all_equipment'))

@app.route('/all_equipment')
@login_required
def all_equipment():
    query = Equipment.query
    filters = {}
    for field in ['name', 'company', 'location', 'category', 'creator', 'status']:
        values = request.args.getlist(field)
        if values and values[0]:
            filters[field] = values
    for field, values in filters.items():
        if field == 'creator':
            creator_ids = [user.id for user in User.query.filter(User.username.in_(values)).all()]
            query = query.filter(Equipment.creator_id.in_(creator_ids))
        else:
            query = query.filter(getattr(Equipment, field).in_(values))
    if not current_user.is_admin:
        query = query.filter_by(creator_id=current_user.id)
    equipment_list = query.order_by(Equipment.created_at.desc()).all()
    return render_template('all_equipment.html', equipment_list=equipment_list)

@app.route('/get-suggestions')
@login_required
def get_suggestions():
    field = request.args.get('field')
    query = request.args.get('q', '')
    if not field or not query:
        return jsonify([])
    field_map = {'name': Equipment.name, 'company': Equipment.company, 'location': Equipment.location, 'category': Equipment.category, 'model': Equipment.model, 'serial_number': Equipment.serial_number}
    if field not in field_map:
        return jsonify([])
    results = db.session.query(field_map[field]).filter(field_map[field].ilike(f'%{query}%')).distinct().limit(10).all()
    suggestions = [row[0] for row in results if row[0]]
    return jsonify(suggestions)

@app.route('/get_distinct_values')
@login_required
def get_distinct_values():
    field = request.args.get('field')
    if not field:
        return (jsonify({'error': 'Field parameter is required'}), 400)
    valid_fields = ['name', 'company', 'location', 'category', 'creator']
    if field not in valid_fields:
        return (jsonify({'error': 'Invalid field'}), 400)
    query = None
    if field == 'creator':
        if current_user.is_admin:
            query = db.session.query(User.username.distinct()).all()
        else:
            query = db.session.query(User.username.distinct()).filter(User.id == current_user.id).all()
    elif current_user.is_admin:
        query = db.session.query(getattr(Equipment, field).distinct()).all()
    else:
        query = db.session.query(getattr(Equipment, field).distinct()).filter_by(creator_id=current_user.id).all()
    values = [value[0] for value in query if value[0]]
    return jsonify({'values': sorted(values)})

@app.route('/in-review')
@login_required
@requires_admin
def in_review_equipment():
    equipment_list = Equipment.query.filter_by(status='En revisión').all()
    return render_template('index.html', equipment_list=equipment_list, status_colors={'En revisión': 'warning'})

@app.route('/reviewed')
@login_required
@requires_admin
def reviewed_equipment():
    equipment_list = Equipment.query.filter_by(status='Revisado').all()
    return render_template('index.html', equipment_list=equipment_list, status_colors={'Revisado': 'info'})

@app.route('/rejected')
@login_required
@requires_admin
def rejected_equipment():
    equipment_list = Equipment.query.filter_by(status='Rechazado').order_by(Equipment.created_at.desc()).all()
    rejected_count = len(equipment_list)
    stats = {'total': rejected_count, 'pending': 0, 'reviewed': 0, 'published': 0, 'rejected': rejected_count}
    return render_template('index.html', equipment_list=equipment_list, stats=stats, title='Equipos Rechazados')

@app.route('/published')
@login_required
def published_equipment():
    equipment_list = Equipment.query.filter_by(status='Publicado').all()
    return render_template('index.html', equipment_list=equipment_list, status_colors={'Publicado': 'success'}, title='Equipos Publicados')

@app.route('/my-equipment')
@login_required
def my_equipment():
    equipment_list = Equipment.query.filter_by(creator_id=current_user.id).all()
    status_colors = {'En revisión': 'warning', 'Revisado': 'info', 'Publicado': 'success', 'Rechazado': 'danger'}
    return render_template('index.html', equipment_list=equipment_list, status_colors=status_colors, title='Mis Equipos')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('login'))

@app.route('/add-equipment', methods=['GET', 'POST'])
@login_required
def add_equipment():
    if request.method == 'POST':
        try:
            existing_equipment = Equipment.query.filter_by(category=request.form['category'], serial_number=request.form['serial_number']).first()
            if existing_equipment:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Ya existe un equipo con la misma categoría y número de serie.'})
                flash('Ya existe un equipo con la misma categoría y número de serie.', 'danger')
                return render_template('add_equipment.html')
            equipment = Equipment(company=request.form['company'], name=request.form['name'], model=request.form['model'], category=request.form['category'], serial_number=request.form['serial_number'], quantity=int(request.form['quantity']), unit_price=float(request.form['unit_price']), location=request.form['location'], notes=request.form['notes'], creator_id=current_user.id)
            if current_user.is_admin:
                equipment.status = request.form.get('status', 'En revisión')
                if equipment.status == 'Publicado':
                    equipment.published_at = datetime.utcnow()
            else:
                equipment.status = 'En revisión'
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    equipment.image_filename = filename
            db.session.add(equipment)
            db.session.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Equipo agregado exitosamente', 'redirect': url_for('index')})
            flash('Equipo agregado exitosamente', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Ha ocurrido un error al procesar la solicitud: ' + str(e)})
            flash('Ha ocurrido un error al procesar la solicitud.', 'danger')
            return render_template('add_equipment.html')
    return render_template('add_equipment.html')

@app.route('/equipment/<int:equipment_id>')
@login_required
def equipment_detail(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template('equipment_detail.html', equipment=equipment)

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
            old_quantity = equipment.quantity
            new_quantity = int(request.form.get('quantity', 0))
            quantity_difference = new_quantity - old_quantity
            equipment.name = request.form.get('name')
            equipment.company = request.form.get('company')
            equipment.model = request.form.get('model')
            equipment.category = request.form.get('category')
            equipment.serial_number = request.form.get('serial_number')
            equipment.quantity = new_quantity
            equipment.unit_price = float(request.form.get('unit_price', 0))
            equipment.location = request.form.get('location')
            equipment.notes = request.form.get('notes', '')
            if equipment.available_quantity is None:
                equipment.available_quantity = new_quantity
            else:
                equipment.available_quantity = max(0, equipment.available_quantity + quantity_difference)
            if equipment.available_quantity == 0 and equipment.status == 'Publicado':
                equipment.status = 'Acabado'
                notification = Notification(recipient_id=equipment.creator_id, message=f'Tu producto "{equipment.name}" se ha marcado como agotado.', type='stock_empty')
                db.session.add(notification)
            elif equipment.available_quantity > 0 and equipment.status == 'Acabado':
                equipment.status = 'Publicado'
                notification = Notification(recipient_id=equipment.creator_id, message=f'Tu producto "{equipment.name}" está nuevamente disponible con {equipment.available_quantity} unidades.', type='stock_available')
                db.session.add(notification)
            if 'status' in request.form:
                new_status = request.form['status']
                if new_status != equipment.status:
                    equipment.status = new_status
                    if new_status == 'Publicado':
                        equipment.published_at = datetime.utcnow()
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
            print(f'Error: {str(e)}')
            return render_template('edit_equipment.html', equipment=equipment)
    return render_template('edit_equipment.html', equipment=equipment)

@app.route('/equipment/<int:equipment_id>/delete')
@login_required
def delete_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    if not current_user.is_admin and equipment.creator_id != current_user.id:
        flash('No tienes permiso para eliminar este equipo.', 'danger')
        return redirect(url_for('all_equipment'))
    if equipment.image_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], equipment.image_filename))
        except:
            pass
    db.session.delete(equipment)
    db.session.commit()
    flash('Equipo eliminado exitosamente.', 'success')
    return redirect(url_for('all_equipment'))

@app.route('/manage-users')
@login_required
@requires_admin
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/add-user', methods=['GET', 'POST'])
@login_required
@requires_admin
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        if not username or not password:
            flash('Por favor complete todos los campos.', 'danger')
            return redirect(url_for('add_user'))
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return redirect(url_for('add_user'))
        try:
            new_user = User(username=username, is_admin=is_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el usuario: {str(e)}', 'danger')
            return redirect(url_for('add_user'))
    return render_template('add_user.html')

@app.route('/edit-user/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_admin
def edit_user(id):
    user = User.query.get_or_404(id)
    if user.username == 'admin':
        flash('No se puede editar el usuario admin.', 'danger')
        return redirect(url_for('manage_users'))
    if request.method == 'POST':
        new_password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        try:
            if new_password:
                user.set_password(new_password)
            user.is_admin = is_admin
            db.session.commit()
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el usuario: {str(e)}', 'danger')
    return render_template('edit_user.html', user=user)

@app.route('/delete-user/<int:id>')
@login_required
@requires_admin
def delete_user(id):
    if current_user.id == id:
        flash('No puedes eliminar tu propio usuario.', 'danger')
        return redirect(url_for('manage_users'))
    user = User.query.get_or_404(id)
    if user.username == 'admin':
        flash('No se puede eliminar el usuario admin.', 'danger')
        return redirect(url_for('manage_users'))
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el usuario: {str(e)}', 'danger')
    return redirect(url_for('manage_users'))

@app.route('/equipment/<int:equipment_id>/reserve', methods=['POST'])
@login_required
def reserve_equipment(equipment_id):
    if current_user.is_admin:
        flash('Los administradores no pueden realizar reservas.', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))
    equipment = Equipment.query.get_or_404(equipment_id)
    if equipment.creator_id == current_user.id:
        flash('No puedes reservar tu propio equipo.', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))
    quantity = int(request.form.get('quantity', 1))
    if quantity <= 0:
        flash('La cantidad debe ser mayor que 0.', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))
    if quantity > equipment.available_quantity:
        flash('No hay suficiente cantidad disponible.', 'error')
        return redirect(url_for('equipment_detail', equipment_id=equipment_id))
    transaction = Transaction(equipment_id=equipment.id, buyer_id=current_user.id, seller_id=equipment.creator_id, quantity=quantity, unit_price=equipment.unit_price, status='Pendiente')
    equipment.available_quantity -= quantity
    notification = Notification(recipient_id=equipment.creator_id, message=f'Nueva solicitud de reserva para {equipment.name} por {current_user.username}', type='reservation', transaction_id=transaction.id)
    try:
        db.session.add(transaction)
        db.session.add(notification)
        db.session.commit()
        flash('Solicitud de reserva enviada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar la reserva.', 'error')
        print(f'Error: {str(e)}')
    return redirect(url_for('equipment_detail', equipment_id=equipment_id))

@app.route('/transactions')
@login_required
def transactions():
    if current_user.is_admin:
        all_transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
        return render_template('transactions.html', all_transactions=all_transactions)
    else:
        purchases = Transaction.query.filter_by(buyer_id=current_user.id).order_by(Transaction.created_at.desc()).all()
        sales = Transaction.query.filter_by(seller_id=current_user.id).order_by(Transaction.created_at.desc()).all()
        return render_template('transactions.html', purchases=purchases, sales=sales)

@app.route('/my-transactions')
@login_required
def my_transactions():
    my_reservations = Transaction.query.options(db.joinedload(Transaction.equipment)).options(db.joinedload(Transaction.seller)).filter(Transaction.buyer_id == current_user.id).order_by(Transaction.created_at.desc()).all()
    return render_template('my_transactions.html', transactions=my_reservations)

@app.route('/my-sales')
@login_required
def my_sales():
    my_sales = Transaction.query.options(db.joinedload(Transaction.equipment)).options(db.joinedload(Transaction.buyer)).filter(Transaction.seller_id == current_user.id).order_by(Transaction.created_at.desc()).all()
    return render_template('my_sales.html', transactions=my_sales)

@app.route('/transactions/<int:transaction_id>/cancel', methods=['POST'])
@login_required
def cancel_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if not (current_user.is_admin or ((current_user.id == transaction.buyer_id or current_user.id == transaction.seller_id) and transaction.status == 'Pendiente')):
        flash('No tienes permiso para cancelar esta transacción.', 'error')
        return redirect(url_for('transactions'))
    if transaction.status != 'Pendiente':
        flash('Solo se pueden cancelar transacciones pendientes.', 'error')
        return redirect(url_for('transactions'))
    try:
        equipment = transaction.equipment
        equipment.available_quantity += transaction.quantity
        transaction.status = 'Cancelado'
        if current_user.is_admin:
            buyer_msg = f'Un administrador ha cancelado tu reserva de {transaction.quantity} unidad(es) de {equipment.name}'
            seller_msg = f'Un administrador ha cancelado la reserva de {transaction.quantity} unidad(es) de {equipment.name} por {transaction.buyer.username}'
        else:
            actor = 'comprador' if current_user.id == transaction.buyer_id else 'vendedor'
            buyer_msg = f'El {actor} ha cancelado la reserva de {transaction.quantity} unidad(es) de {equipment.name}'
            seller_msg = buyer_msg
        if current_user.id != transaction.buyer_id:
            buyer_notification = Notification(recipient_id=transaction.buyer_id, message=buyer_msg, type='cancellation', transaction_id=transaction.id)
            db.session.add(buyer_notification)
        if current_user.id != transaction.seller_id:
            seller_notification = Notification(recipient_id=transaction.seller_id, message=seller_msg, type='cancellation', transaction_id=transaction.id)
            db.session.add(seller_notification)
        db.session.commit()
        flash('Transacción cancelada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al cancelar la transacción.', 'error')
        print(f'Error: {str(e)}')
    return redirect(url_for('transactions'))

@app.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(recipient_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.recipient_id != current_user.id:
        abort(403)
    notification.read = True
    db.session.commit()
    return redirect(url_for('notifications'))