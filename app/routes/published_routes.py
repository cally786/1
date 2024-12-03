from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models.models import Equipment, Transaction

published = Blueprint('published', __name__)

@published.route('/published')
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
