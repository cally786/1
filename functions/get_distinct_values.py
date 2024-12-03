from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/get_distinct_values')
@login_required
def get_distinct_values():
    field = request.args.get('field')
    if not field:
        return jsonify({'error': 'Field parameter is required'}), 400

    valid_fields = ['name', 'company', 'location', 'category', 'creator']
    if field not in valid_fields:
        return jsonify({'error': 'Invalid field'}), 400

    query = None
    if field == 'creator':
        # Get distinct usernames for creators
        if current_user.is_admin:
            query = db.session.query(User.username.distinct()).all()
        else:
            query = db.session.query(User.username.distinct()).filter(User.id == current_user.id).all()
    else:
        # Get distinct values for other fields
        if current_user.is_admin:
            query = db.session.query(getattr(Equipment, field).distinct()).all()
        else:
            query = db.session.query(getattr(Equipment, field).distinct()).filter_by(creator_id=current_user.id).all()

    values = [value[0] for value in query if value[0]]  # Filter out None values
    return jsonify({'values': sorted(values)})
