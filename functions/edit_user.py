from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


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
            # Actualizar contraseña solo si se proporcionó una nueva
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
