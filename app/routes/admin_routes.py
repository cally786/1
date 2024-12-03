from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.models import Equipment, Transaction
from app.utils.helpers import requires_admin

admin = Blueprint('admin', __name__)

@admin.route('/admin/dashboard')
@login_required
@requires_admin
def dashboard():
    # Obtener estadísticas generales
    stats = {
        'total_equipment': Equipment.query.count(),
        'available_equipment': Equipment.query.filter_by(status='Publicado').count(),
        'in_review_equipment': Equipment.query.filter_by(status='En revisión').count(),
        'rejected_equipment': Equipment.query.filter_by(status='Rechazado').count(),
        'pending_transactions': Transaction.query.filter_by(status='Pendiente').count()
    }
    
    # Obtener todos los equipos para el admin
    equipment_list = Equipment.query.order_by(Equipment.created_at.desc()).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         equipment_list=equipment_list,
                         title='Panel de Control')

@admin.route('/admin/equipment/<status>')
@login_required
@requires_admin
def filter_equipment(status):
    # Obtener equipos filtrados por estado
    equipment_list = Equipment.query.filter_by(status=status).order_by(Equipment.created_at.desc()).all()
    
    # Calcular estadísticas
    stats = {
        'total_equipment': Equipment.query.count(),
        'available_equipment': Equipment.query.filter_by(status='Publicado').count(),
        'in_review_equipment': Equipment.query.filter_by(status='En revisión').count(),
        'rejected_equipment': Equipment.query.filter_by(status='Rechazado').count(),
        'pending_transactions': Transaction.query.filter_by(status='Pendiente').count()
    }
    
    status_colors = {
        'En revisión': 'warning',
        'Revisado': 'info',
        'Publicado': 'success',
        'Rechazado': 'danger'
    }
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         equipment_list=equipment_list,
                         status_colors=status_colors,
                         title=f'Equipos {status}')
