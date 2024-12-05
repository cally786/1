from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models.models import Equipment, Transaction

published = Blueprint('published', __name__)

@published.route('/published')
@login_required
def published_equipment():
    # Para la página de equipos publicados, siempre mostramos solo los publicados
    equipment_list = Equipment.query.filter_by(status='Publicado').all()
    
    # Calcular estadísticas solo de equipos publicados
    stats = {
        'total_equipment': len(equipment_list),
        'status_counts': {
            'Publicado': len(equipment_list)
        }
    }
    
    return render_template('published_equipment.html', 
                         equipment_list=equipment_list,
                         stats=stats,
                         show_actions=False,  # No mostrar acciones en la vista pública
                         title='Equipos Disponibles')
