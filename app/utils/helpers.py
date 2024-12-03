# utils/helpers.py

from functools import wraps
from flask import request, url_for, flash, redirect
from flask_login import current_user
from app import app

def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def url_params(**updates):
    """Helper function to update URL parameters while preserving existing ones"""
    args = request.args.copy()
    for key, value in updates.items():
        if value is not None:
            args[key] = value
        elif key in args:
            del args[key]
    return url_for(request.endpoint, **args)

app.jinja_env.globals['url_params'] = url_params

from app.models.models import Notification
from flask_login import current_user

@app.context_processor
def utility_processor():
    def unread_notifications_count():
        if current_user.is_authenticated:
            return Notification.query.filter_by(recipient_id=current_user.id, read=False).count()
        return 0
    
    return dict(unread_notifications_count=unread_notifications_count())
