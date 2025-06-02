from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(message='نام کاربری الزامی است')])
    password = PasswordField('رمز عبور', validators=[DataRequired(message='رمز عبور الزامی است')])
    remember_me = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود')

class CommentForm(FlaskForm):
    comment = TextAreaField('متن نظر', validators=[
        DataRequired(message='متن نظر الزامی است'),
        Length(min=3, max=1000, message='متن نظر باید بین 3 تا 1000 کاراکتر باشد')
    ])
    submit = SubmitField('ثبت نظر')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('رمز عبور فعلی', validators=[
        DataRequired(message='رمز عبور فعلی الزامی است')
    ])
    new_password = PasswordField('رمز عبور جدید', validators=[
        DataRequired(message='رمز عبور جدید الزامی است'),
        Length(min=8, message='رمز عبور باید حداقل 8 کاراکتر باشد')
    ])
    confirm_password = PasswordField('تکرار رمز عبور جدید', validators=[
        DataRequired(message='تکرار رمز عبور الزامی است'),
        EqualTo('new_password', message='رمز عبور و تکرار آن باید یکسان باشند')
    ])
    submit = SubmitField('تغییر رمز عبور') 