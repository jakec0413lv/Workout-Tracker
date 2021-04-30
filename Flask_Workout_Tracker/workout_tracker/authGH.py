import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from workout_tracker.db import get_db

from email.mime.text import MIMEText
import smtplib
import string
import random

def send_email(email, reset_code):
    from_email="-------"
    from_password="------"
    to_email=email

    subject="Password Reset"
    message="Your code to reset you password is " + reset_code + "!"

    msg=MIMEText(message, 'html')
    msg['Subject']=subject
    msg['To']=to_email
    msg['From']=from_email

    gmail=smtplib.SMTP('smtp.gmail.com', 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email, from_password)
    gmail.send_message(msg)


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/forgotPW', methods=('GET', 'POST'))
def forgotPW():
    if request.method == 'POST':
        username = request.form['username']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Username not registered.'

        if error is None:
            letters = string.ascii_lowercase
            global reset_code
            global reset_username
            reset_username = user['username']
            reset_code = 'as324dasf'
            send_email(user['username'], reset_code)
            return redirect(url_for('auth.resetPW'))

        flash(error)

    return render_template('auth/forgotPW.html')

@bp.route('/resetPW', methods=('GET', 'POST'))
def resetPW():
    if request.method == 'POST':
        username = request.form['username']
        user_reset_code = request.form['reset-code']
        user_new_password = request.form["new-password"]
        error = None

        if username != reset_username:
            error = 'Invalid username.'

        if user_reset_code != reset_code:
            error = 'Invalid reset code.'

        if error is None: 
            db = get_db()
            db.execute(
                'UPDATE user SET password = ?'
                'WHERE username = ?',
                (generate_password_hash(user_new_password), username)
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/resetPW.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view