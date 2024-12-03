from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/')
@login_required
def index():
    # For admin users, show all equipment except rejected ones
    if current_user.is_admin:
        equipment_list = Equipment.query.filter(
            Equipment.status != 'Rechazado'
        ).order_by(Equipment.created_at.desc()).all()
        
        # Calculate stats for non-rejected equipment
        total = Equipment.query.filter(Equipment.status != 'Rechazado').count()
        pending = Equipment.query.filter_by(status='En revisión').count()
        reviewed = Equipment.query.filter_by(status='Revisado').count()
        published = Equipment.query.filter_by(status='Publicado').count()
        
        stats = {
            'total': total,
            'pending': pending,
            'reviewed': reviewed,
            'published': published
        }
    else:
        # For regular users, show only their equipment
        equipment_list = Equipment.query.filter_by(
            creator_id=current_user.id
        ).order_by(Equipment.created_at.desc()).all()
        
        # Calculate stats for user's equipment
        total = Equipment.query.filter_by(creator_id=current_user.id).count()
        pending = Equipment.query.filter_by(creator_id=current_user.id, status='En revisión').count()
        reviewed = Equipment.query.filter_by(creator_id=current_user.id, status='Revisado').count()
        published = Equipment.query.filter_by(creator_id=current_user.id, status='Publicado').count()
        
        stats = {
            'total': total,
            'pending': pending,
            'reviewed': reviewed,
            'published': published
        }
    
    return render_template('index.html', 
                         equipment_list=equipment_list,
                         stats=stats,
                         title='Panel de Control')
