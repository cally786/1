# routes/main_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, LoginManager
from app import app, db
from app.models.models import Equipment, User, Transaction, Notification, Category
from app.utils.helpers import requires_admin
from sqlalchemy import desc, func
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Si el usuario es admin, redirigir al dashboard
    if current_user.is_authenticated and current_user.is_admin:
        # Obtener conteo de equipos por estado
        status_counts = db.session.query(
            Equipment.status, 
            func.count(Equipment.id)
        ).group_by(Equipment.status).all()
        
        # Asegurar que todos los estados posibles estén incluidos
        all_statuses = ['En revisión', 'Revisado', 'Publicado', 'Rechazado', 'Agotado', 'Disponible', 'En préstamo']
        status_stats = {status: 0 for status in all_statuses}  # Inicializar todos en 0
        
        # Actualizar con los conteos reales
        for status, count in status_counts:
            if status in status_stats:
                status_stats[status] = count
        
        stats = {
            'total_equipment': sum(status_stats.values()),
            'status_counts': status_stats,
            'pending_transactions': Transaction.query.filter_by(status='Pendiente').count(),
            'active_transactions': Transaction.query.filter_by(status='Activo').count(),
            'total_users': User.query.filter_by(is_admin=False).count()
        }
        
        # Obtener transacciones pendientes
        pending_transactions = Transaction.query.filter_by(status='Pendiente').all()
        
        return render_template('index.html', 
                             stats=stats,
                             pending_transactions=pending_transactions)
    
    # Para usuarios normales y no autenticados, mostrar landing page
    equipment_count = Equipment.query.filter_by(status='Disponible').count()
    active_transactions = Transaction.query.filter_by(status='Activo').count()
    user_count = User.query.filter_by(is_admin=False).count()
    
    return render_template('landing.html',
                         equipment_count=equipment_count,
                         active_loans=active_transactions,  
                         user_count=user_count)

@main.route('/dashboard')
@login_required
@requires_admin
def dashboard():
    # Estadísticas generales
    total_equipment = Equipment.query.count()
    total_transactions = Transaction.query.count()
    pending_transactions = Transaction.query.filter_by(status='Pendiente').count()
    
    return render_template(
        'dashboard.html',
        total_equipment=total_equipment,
        total_transactions=total_transactions,
        pending_transactions=pending_transactions
    )

@main.route('/all-equipment')
@login_required
def all_equipment_redirect():
    return redirect(url_for('main.all_equipment'))
