import os
from flask import (
    Blueprint, render_template, request, jsonify,
    redirect, url_for, flash, send_file
)
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from .forms import UploadForm, LoginForm, RegisterForm, ProfileForm, PasswordUpdateForm
from .models import User, History, db
from .anonymise import anonymise_text, extract_text_from_file
from datetime import datetime

main = Blueprint('main', __name__)

def is_api_error(text):
    """Returns True if the output is an API or config error."""
    if not text:
        return True
    low = text.lower()
    return (
        low.startswith("error:") or
        "api key not set" in low or
        "cannot use advanced models" in low
    )

# ---------- INDEX PAGE ----------
@main.route("/", methods=["GET", "POST"])
def index():
    form = UploadForm()
    anonymised_text = ""
    message = ""
    input_text = ""
    can_save = False
    if request.method == "POST":
        # AJAX request
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            text = request.form.get("text", "").strip()
            level = request.form.get("level", "low")
            model = request.form.get("model", "spacy")
            user = current_user if current_user.is_authenticated else None
            file = request.files.get("file")
            filename = file.filename if file and file.filename else ""
            if file and not text:
                text = extract_text_from_file(file)
                input_text = text
            else:
                input_text = text

            anonymised_text = ""
            message = ""
            can_save = False
            is_guest = not (user and user.is_authenticated)

            # Run anonymisation logic
            if not text:
                anonymised_text = ""
                message = "Please provide text or upload a file."
            else:
                if is_guest:
                    if model != "spacy":
                        anonymised_text = "Guest users cannot use advanced models. Login or create an account to add your API key and access faster models."
                        message = ""
                    else:
                        anonymised_text = anonymise_text(text, level, model, user)
                        message = "Anonymisation complete! Log in to save your reports and download in PDF or text."
                else:
                    if model == "openai" and not user.openai_api_key:
                        anonymised_text = "Error: OpenAI API key not set. Add your API key in your profile to use this model."
                        message = ""
                    elif model in ("hf_mistral", "hf_falcon", "hf_llama") and not user.hf_api_key:
                        anonymised_text = "Error: Hugging Face API key not set. Add your API key in your profile to use this model."
                        message = ""
                    else:
                        anonymised_text = anonymise_text(text, level, model, user)
                        message = ""

            # Only allow save for logged in users with non-error, non-duplicate output
            if (
                not is_guest and anonymised_text and
                not is_api_error(anonymised_text) and
                anonymised_text != text
            ):
                can_save = True

            return jsonify({
                "anonymised_text": anonymised_text,
                "message": message,
                "model_used": model,
                "is_guest": is_guest,
                "can_save": bool(can_save),
                "input_text": input_text,
                "level": level,
                "filename": filename
            })

        # Classic POST (non-AJAX)
        text = form.text.data or ""
        input_text = text
        level = form.level.data
        model = form.model.data
        file = form.file.data
        filename = file.filename if file and file.filename else ""
        user = current_user if current_user.is_authenticated else None
        can_save = False
        anonymised_text = ""
        message = ""
        is_guest = not (user and user.is_authenticated)
        if file and not text:
            text = extract_text_from_file(file)
            input_text = text
        if not text:
            anonymised_text = ""
            message = "Please provide text or upload a file."
        else:
            if is_guest:
                if model != "spacy":
                    anonymised_text = "Guest users cannot use advanced models. Login or create an account to add your API key and access faster models."
                    message = ""
                else:
                    anonymised_text = anonymise_text(text, level, model, user)
                    message = "Anonymisation complete! Log in to save your reports and download in PDF or text."
            else:
                if model == "openai" and not user.openai_api_key:
                    anonymised_text = "Error: OpenAI API key not set. Add your API key in your profile to use this model."
                    message = ""
                elif model in ("hf_mistral", "hf_falcon", "hf_llama") and not user.hf_api_key:
                    anonymised_text = "Error: Hugging Face API key not set. Add your API key in your profile to use this model."
                    message = ""
                else:
                    anonymised_text = anonymise_text(text, level, model, user)
                    message = ""
        if (
            not is_guest and anonymised_text and
            not is_api_error(anonymised_text) and
            anonymised_text != text
        ):
            can_save = True
        return render_template(
            "index.html",
            form=form,
            anonymised_text=anonymised_text,
            input_text=input_text,
            message=message,
            model_used=model,
            is_guest=is_guest,
            can_save=bool(can_save),
            level=level,
            filename=filename
        )
    return render_template(
        "index.html",
        form=form,
        anonymised_text="",
        input_text="",
        message="",
        model_used="spacy",
        is_guest=not (current_user.is_authenticated),
        can_save=False,
        level="low",
        filename=""
    )

# ---------- SAVE REPORT (AJAX) ----------
@main.route("/save-report", methods=["POST"])
@login_required
def save_report():
    # Accept JSON (AJAX) and form data (fallback)
    if request.is_json:
        data = request.get_json()
        text = data.get("input_text", "").strip()
        anonymised_text = data.get("anonymised_text", "").strip()
        level = data.get("level", "low")
        model = data.get("model_used", "spacy")
        filename = data.get("filename", "")
    else:
        text = request.form.get("input_text", "").strip()
        anonymised_text = request.form.get("anonymised_text", "").strip()
        level = request.form.get("level", "low")
        model = request.form.get("model_used", "spacy")
        filename = request.form.get("filename", "")

    # Only save if: not empty, not error, not identical to input, user is authenticated
    if not text or not anonymised_text or anonymised_text == text or is_api_error(anonymised_text):
        return jsonify({"success": False, "msg": "Nothing to save"}), 400

    history = History(
        input_text=text,
        anonymised_text=anonymised_text,
        anonymisation_level=level,
        model_used=model,
        input_filename=filename,
        timestamp=datetime.utcnow(),
        user_id=current_user.id
    )
    db.session.add(history)
    db.session.commit()
    return jsonify({"success": True, "msg": "Report saved!", "history_id": history.id})

# ---------- FILE EXTRACT ROUTE ----------
@main.route("/extract", methods=["POST"])
def extract():
    file = request.files.get("file")
    if file:
        text = extract_text_from_file(file)
        return jsonify({"text": text})
    return jsonify({"text": ""})

# ---------- LOGIN ----------
@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html", form=form)

# ---------- LOGOUT ----------
@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

# ---------- REGISTER ----------
@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        # Check for unique username or email
        existing_user = User.query.filter(
            (User.username == form.username.data.strip()) | (User.email == form.email.data.strip())
        ).first()
        if existing_user:
            if existing_user.username == form.username.data.strip():
                flash("Username is already taken. Please choose another.", "danger")
            elif existing_user.email == form.email.data.strip():
                flash("Email is already registered. Please use a different email.", "danger")
            return render_template("register.html", form=form)

        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip()
        )
        user.set_password(form.password.data)
        user.openai_api_key = form.openai_api_key.data.strip()
        user.hf_api_key = form.hf_api_key.data.strip()
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)

# ---------- DASHBOARD (History) ----------
@main.route("/dashboard")
@login_required
def dashboard():
    page = request.args.get("page", 1, type=int)
    histories = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template("dashboard.html", histories=histories)

# ---------- VIEW HISTORY ----------
@main.route("/history/<int:history_id>")
@login_required
def view_history(history_id):
    history = History.query.filter_by(id=history_id, user_id=current_user.id).first_or_404()
    return render_template("view_history.html", history=history)

# ---------- PROFILE ----------
@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    update_flags = []
    if form.validate_on_submit():
        # Check and update email
        if hasattr(form, "email") and form.email.data.strip() != current_user.email:
            current_user.email = form.email.data.strip()
            update_flags.append("Email")
        # Check and update OpenAI API key
        if hasattr(form, "openai_api_key") and (form.openai_api_key.data or "").strip() != (current_user.openai_api_key or ""):
            current_user.openai_api_key = (form.openai_api_key.data or "").strip()
            update_flags.append("OpenAI API key")
        # Check and update HuggingFace API key
        if hasattr(form, "hf_api_key") and (form.hf_api_key.data or "").strip() != (current_user.hf_api_key or ""):
            current_user.hf_api_key = (form.hf_api_key.data or "").strip()
            update_flags.append("Hugging Face API key")
        db.session.commit()
        if update_flags:
            flash("Updated: " + ", ".join(update_flags), "success")
        else:
            flash("No changes detected.", "info")
        return redirect(url_for("main.profile"))
    return render_template("profile.html", form=form)

# ---------- CHANGE PASSWORD ----------
@main.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = PasswordUpdateForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash("Current password incorrect.", "danger")
        elif form.new_password.data != form.confirm_password.data:
            flash("New passwords do not match.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for("main.profile"))
    return render_template("change_password.html", form=form)

# ---------- DELETE HISTORY ----------
@main.route("/delete/<int:history_id>", methods=["POST"])
@login_required
def delete_history(history_id):
    history = History.query.filter_by(id=history_id, user_id=current_user.id).first_or_404()
    db.session.delete(history)
    db.session.commit()
    return jsonify({"success": True})

# ---------- DOWNLOAD ----------
@main.route("/download/<int:history_id>/<format>")
@login_required
def download_anonymised(history_id, format):
    history = History.query.filter_by(id=history_id, user_id=current_user.id).first_or_404()
    from .utils import export_as_docx_or_pdf, export_as_txt
    if format == "pdf" or format == "docx":
        output = export_as_docx_or_pdf(history.anonymised_text, format)
        filename = f"anonymised_report_{history_id}.{format}"
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=filename)
    elif format == "txt":
        output = export_as_txt(history.anonymised_text)
        filename = f"anonymised_report_{history_id}.txt"
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=filename)
    else:
        return "Invalid format", 400
