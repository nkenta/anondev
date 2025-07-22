from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.anonymize_page'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.anonymize_page'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.anonymize_page'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        api_key = request.form.get('api_key')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, openai_api_key=api_key)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # For security, verify current password before making any changes
        current_password = request.form.get('current_password')
        if not current_user.check_password(current_password):
            flash('Your current password is not correct. No changes were saved.', 'danger')
            return redirect(url_for('auth.profile'))

        changes_made = []

        # --- Logic to handle API Key change ---
        new_api_key = request.form.get('api_key')
        # Check if the API key has actually changed
        if new_api_key != (current_user.openai_api_key or ''):
            current_user.openai_api_key = new_api_key
            changes_made.append("API Key")

        # --- Logic to handle Password change ---
        new_password = request.form.get('new_password')
        # Only proceed if the user entered a new password
        if new_password:
            confirm_new_password = request.form.get('confirm_new_password')
            if len(new_password) < 8:
                flash('Password must be at least 8 characters long. No changes were saved.', 'danger')
                return redirect(url_for('auth.profile'))
            if new_password != confirm_new_password:
                flash('The new password and confirmation password do not match. No changes were saved.', 'danger')
                return redirect(url_for('auth.profile'))

            # If all checks pass, set the new password
            current_user.set_password(new_password)
            changes_made.append("Password")

        # --- Finalize and provide feedback ---
        if not changes_made:
            flash('No changes were detected.', 'info')
        else:
            db.session.commit()
            # Construct a dynamic success message
            success_message = f"Your {' and '.join(changes_made)} has been updated successfully!"
            flash(success_message, 'success')

        return redirect(url_for('auth.profile'))

    # For GET requests, just render the page
    return render_template('profile.html', user=current_user)