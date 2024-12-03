from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/get-suggestions')
@login_required
def get_suggestions():
    field = request.args.get('field')
    query = request.args.get('q', '')
    
    if not field or not query:
        return jsonify([])
    
    # Mapeo de campos a columnas de la base de datos
    field_map = {
        'name': Equipment.name,
        'company': Equipment.company,
        'location': Equipment.location,
        'category': Equipment.category,
        'model': Equipment.model,
        'serial_number': Equipment.serial_number
    }
    
    if field not in field_map:
        return jsonify([])
    
    # Realizar la búsqueda
    results = db.session.query(field_map[field])\
        .filter(field_map[field].ilike(f'%{query}%'))\
        .distinct()\
        .limit(10)\
        .all()
    
    # Extraer los valores únicos
    suggestions = [row[0] for row in results if row[0]]
    
    return jsonify(suggestions)
