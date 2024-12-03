from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(recipient_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=user_notifications)
