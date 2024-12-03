from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/rejected')
@login_required
@requires_admin
def rejected_equipment():
    # Get only rejected equipment
    equipment_list = Equipment.query.filter_by(status='Rechazado').order_by(Equipment.created_at.desc()).all()
    
    # For rejected view, only show the count of rejected items
    rejected_count = len(equipment_list)
    stats = {
        'total': rejected_count,  # Total is the same as rejected count
        'pending': 0,  # Hide other stats
        'reviewed': 0,
        'published': 0,
        'rejected': rejected_count  # Add rejected count
    }
    
    return render_template('index.html', 
                         equipment_list=equipment_list,
                         stats=stats,
                         title='Equipos Rechazados')
