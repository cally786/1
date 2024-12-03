from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/in-review')
@login_required
@requires_admin
def in_review_equipment():
    equipment_list = Equipment.query.filter_by(status='En revisión').all()
    return render_template('index.html', 
                         equipment_list=equipment_list,
                         status_colors={'En revisión': 'warning'})
