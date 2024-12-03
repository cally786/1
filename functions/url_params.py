from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


def url_params(**updates):
    """Helper function to update URL parameters while preserving existing ones"""
    args = request.args.copy()
    for key, value in updates.items():
        if value is not None:
            args[key] = value
        elif key in args:
            del args[key]
    return url_for(request.endpoint, **args)
