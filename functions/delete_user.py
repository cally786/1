from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


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
