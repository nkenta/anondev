import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response, abort
from flask_login import login_required, current_user
from . import db
from .models import ReportHistory
from .helpers import (
    extract_text_from_file, process_text_spacy,
    finalize_anonymization_text, anonymize_text_with_gpt,
    generate_pdf_report, generate_docx_report
)

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/anonymize')
@login_required
def anonymize_page():
    return render_template('anonymize.html')


@main.route('/upload-file', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        try:
            text = extract_text_from_file(file)
            return jsonify({'text': text})
        except Exception as e:
            return jsonify({'error': f'Failed to process file: {str(e)}'}), 500
    return jsonify({'error': 'File processing failed'}), 500


@main.route('/process-text', methods=['POST'])
@login_required
def process_text():
    data = request.get_json()
    text = data.get('text')
    level = data.get('level')
    if not text or not level:
        return jsonify({'error': 'Missing text or anonymization level.'}), 400

    try:
        entities_to_review = process_text_spacy(text, level)
        return jsonify(entities_to_review)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main.route('/anonymize-text', methods=['POST'])
@login_required
def anonymize_text():
    data = request.get_json()
    model = data.get('model')

    if model == 'spacy':
        original_text = data.get('original_text')
        user_choices = data.get('choices')
        if not original_text or user_choices is None:
            return jsonify({'error': 'Missing data for SpaCy anonymization.'}), 400
        result = finalize_anonymization_text(original_text, user_choices)
        return jsonify(result)

    elif model == 'chatgpt':
        original_text = data.get('original_text')
        level = data.get('level')
        if not current_user.openai_api_key:
            return jsonify({'error': 'OpenAI API key is not set. Please add it in your profile.'}), 400
        if not original_text or not level:
            return jsonify({'error': 'Missing text or level for ChatGPT anonymization.'}), 400

        try:
            result = anonymize_text_with_gpt(original_text, level, current_user.openai_api_key)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid model selected.'}), 400

@main.route('/save-report', methods=['POST'])
@login_required
def save_report():
    data = request.get_json()
    try:
        new_report = ReportHistory(
            original_text=data['original_text'],
            anonymized_text_highlighted=data['anonymized_text_highlighted'],
            anonymized_text_clean=data['anonymized_text_clean'],
            user_id=current_user.id,
            # --- NEW DATA BEING SAVED ---
            model_used=data['model'],
            anonymization_level=data['level']
        )
        db.session.add(new_report)
        db.session.commit()
        flash('Report saved successfully!', 'success')
        return jsonify({'success': True, 'redirect_url': url_for('main.history')})
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    user_reports = ReportHistory.query.filter_by(user_id=current_user.id).order_by(
        ReportHistory.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('history.html', reports=user_reports)


@main.route('/history/<int:report_id>')
@login_required
def history_detail(report_id):
    report = ReportHistory.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        abort(403)
    return render_template('history_detail.html', report=report)


@main.route('/history/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_history(report_id):
    report = ReportHistory.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        abort(403)
    db.session.delete(report)
    db.session.commit()
    flash('History entry deleted successfully.', 'success')
    return redirect(url_for('main.history'))


@main.route('/download/<int:report_id>/<string:file_format>/<string:highlight>')
@login_required
def download_report(report_id, file_format, highlight):
    report = ReportHistory.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        abort(403)

    use_highlight = highlight == 'true'
    text_content = report.anonymized_text_highlighted if use_highlight else report.anonymized_text_clean

    if file_format == 'pdf':
        pdf_buffer = generate_pdf_report(text_content, use_highlight)
        return Response(pdf_buffer, mimetype='application/pdf',
                        headers={'Content-Disposition': f'attachment;filename=report_{report_id}.pdf'})
    elif file_format == 'docx':
        docx_buffer = generate_docx_report(text_content, use_highlight)
        return Response(docx_buffer, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        headers={'Content-Disposition': f'attachment;filename=report_{report_id}.docx'})
    else:
        abort(404)