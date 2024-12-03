# routes/user_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import User
from app.utils.helpers import requires_admin
from app import db

user = Blueprint('user', __name__)

@user.route('/users')
@login_required
@requires_admin
def list_users():
    users = User.query.all()
    return render_template('users/list.html', users=users)

@user.route('/users/<int:user_id>')
@login_required
@requires_admin
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('users/detail.html', user=user)

@user.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@requires_admin
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('No puedes cambiar tu propio estado de administrador.', 'error')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'Estado de administrador actualizado para {user.username}.', 'success')
    return redirect(url_for('user.list_users'))

@user.route('/add-user', methods=['GET', 'POST'])
@login_required
@requires_admin
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        if not username or not password:
            flash('Por favor complete todos los campos.', 'danger')
            return redirect(url_for('user.add_user'))
        
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return redirect(url_for('user.add_user'))
        
        try:
            new_user = User(username=username, is_admin=is_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('user.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el usuario: {str(e)}', 'danger')
            return redirect(url_for('user.add_user'))
    
    return render_template('add_user.html')

@user.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@requires_admin
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.username == 'admin':
        flash('No se puede editar el usuario admin.', 'danger')
        return redirect(url_for('user.list_users'))
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        try:
            # Actualizar contraseña solo si se proporcionó una nueva
            if new_password:
                user.set_password(new_password)
            
            user.is_admin = is_admin
            db.session.commit()
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('user.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el usuario: {str(e)}', 'danger')
    
    return render_template('edit_user.html', user=user)

@user.route('/delete-user/<int:user_id>')
@login_required
@requires_admin
def delete_user(user_id):
    if current_user.id == user_id:
        flash('No puedes eliminar tu propio usuario.', 'danger')
        return redirect(url_for('user.list_users'))
    
    user = User.query.get_or_404(user_id)
    
    if user.username == 'admin':
        flash('No se puede eliminar el usuario admin.', 'danger')
        return redirect(url_for('user.list_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el usuario: {str(e)}', 'danger')
    
    return redirect(url_for('user.list_users'))

@user.route('/profile')
@login_required
def profile():
    return render_template('users/profile.html', user=current_user)

@user.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('Por favor complete todos los campos.', 'danger')
        return redirect(url_for('user.profile'))
    
    if not current_user.check_password(current_password):
        flash('La contraseña actual es incorrecta.', 'danger')
        return redirect(url_for('user.profile'))
    
    if new_password != confirm_password:
        flash('Las contraseñas nuevas no coinciden.', 'danger')
        return redirect(url_for('user.profile'))
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Contraseña actualizada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar la contraseña.', 'danger')
    
    return redirect(url_for('user.profile'))
