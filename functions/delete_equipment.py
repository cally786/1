from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/equipment/<int:equipment_id>/delete')
@login_required
def delete_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Verificar si el usuario tiene permiso para eliminar
    if not current_user.is_admin and equipment.creator_id != current_user.id:
        flash('No tienes permiso para eliminar este equipo.', 'danger')
        return redirect(url_for('all_equipment'))
    
    # Eliminar la imagen si existe
    if equipment.image_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], equipment.image_filename))
        except:
            pass
    
    db.session.delete(equipment)
    db.session.commit()
    flash('Equipo eliminado exitosamente.', 'success')
    return redirect(url_for('all_equipment'))
