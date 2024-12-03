from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/all_equipment')
@login_required
def all_equipment():
    query = Equipment.query

    # Get filter parameters (now supporting multiple values)
    filters = {}
    for field in ['name', 'company', 'location', 'category', 'creator', 'status']:
        values = request.args.getlist(field)
        if values and values[0]:  # Check if there are any non-empty values
            filters[field] = values

    # Apply filters
    for field, values in filters.items():
        if field == 'creator':
            creator_ids = [user.id for user in User.query.filter(User.username.in_(values)).all()]
            query = query.filter(Equipment.creator_id.in_(creator_ids))
        else:
            query = query.filter(getattr(Equipment, field).in_(values))

    # Get equipment list
    if not current_user.is_admin:
        query = query.filter_by(creator_id=current_user.id)
    
    equipment_list = query.order_by(Equipment.created_at.desc()).all()
    return render_template('all_equipment.html', equipment_list=equipment_list)
