from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    description = TextAreaField('Description', validators=[Length(max=200)])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

class BudgetForm(FlaskForm):
    month = IntegerField('Month (1-12)', validators=[DataRequired(), NumberRange(min=1, max=12)])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    amount_limit = FloatField('Budget Limit', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Set Budget')