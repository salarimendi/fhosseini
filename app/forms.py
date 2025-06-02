from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(message='نام کاربری الزامی است')])
    password = PasswordField('رمز عبور', validators=[DataRequired(message='رمز عبور الزامی است')])
    remember_me = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود') 