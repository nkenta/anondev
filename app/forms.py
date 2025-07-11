from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, FileField,
    SelectField, TextAreaField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    openai_api_key = StringField('OpenAI API Key (optional)', validators=[Optional()])
    hf_api_key = StringField('HuggingFace API Key (optional)', validators=[Optional()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UploadForm(FlaskForm):
    file = FileField('Upload File')
    text = TextAreaField('Or Paste Text Here')
    level = SelectField('Anonymisation Level', choices=[
        ('low', 'Low (Basic - Removes obvious names, emails, etc.)'),
        ('medium', 'Medium (Sensitive - Masks indirect clues, jobs, small locations)'),
        ('high', 'High (Strict - Removes or generalises almost everything identifiable)')
    ])
    model = SelectField('Model', choices=[
        ('spacy', 'spaCy (Basic)'),
        ('openai', 'OpenAI GPT-4o (Advanced)'),
        ('hf_mistral', 'HF Mistral (Advanced)'),
        ('hf_falcon', 'HF Falcon (Advanced)'),
        ('hf_llama', 'HF Llama 3 (Advanced)')
    ])
    submit = SubmitField('Anonymise')

class ProfileForm(FlaskForm):
    username = StringField('Username', render_kw={"readonly": True})
    email = StringField('Email', validators=[DataRequired(), Email()])
    openai_api_key = StringField('OpenAI API Key', validators=[Optional()])
    hf_api_key = StringField('HuggingFace API Key', validators=[Optional()])
    submit = SubmitField('Update Profile')

class PasswordUpdateForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(8, 128)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
