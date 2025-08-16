from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re

def latin_only(form, field):
    """اعتبارسنجی حروف لاتین"""
    pattern = re.compile(r'^[a-zA-Z0-9_.-]+$')
    if not pattern.match(field.data):
        raise ValidationError('لطفاً فقط از حروف لاتین، اعداد و نمادهای مجاز (_.-) استفاده کنید.')

class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(message='نام کاربری الزامی است')])
    password = PasswordField('رمز عبور', validators=[DataRequired(message='رمز عبور الزامی است')])
    remember_me = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود')

class RegisterForm(FlaskForm):
    username = StringField('نام کاربری', validators=[
        DataRequired(message='نام کاربری الزامی است'),
        Length(min=3, message='نام کاربری باید حداقل ۳ کاراکتر باشد'),
        latin_only
    ])
    fullname = StringField('نام کامل', validators=[
        DataRequired(message='نام کامل الزامی است'),
        Length(max=40, message='نام کامل نباید بیشتر از ۴۰ کاراکتر باشد')
    ])
    email = StringField('ایمیل', validators=[
        DataRequired(message='ایمیل الزامی است'),
        Email(message='لطفاً یک ایمیل معتبر وارد کنید')
    ])
    password = PasswordField('رمز عبور', validators=[
        DataRequired(message='رمز عبور الزامی است'),
        Length(min=6, message='رمز عبور باید حداقل ۶ کاراکتر باشد')
    ])
    password_confirm = PasswordField('تکرار رمز عبور', validators=[
        DataRequired(message='تکرار رمز عبور الزامی است'),
        EqualTo('password', message='رمز عبور و تکرار آن باید یکسان باشند')
    ])
    role = SelectField('نقش کاربری', choices=[
        ('user', 'کاربر عادی'),
        ('researcher', 'پژوهشگر'),
        ('reader', 'خواننده')
    ], validators=[DataRequired(message='انتخاب نقش الزامی است')])
    submit = SubmitField('ثبت نام')

    def validate_email(self, field):
        """اعتبارسنجی ایمیل"""
        username, domain = field.data.split('@')
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username) or not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
            raise ValidationError('لطفاً یک ایمیل معتبر با حروف لاتین وارد کنید.')

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
        Length(min=8, message='رمز عبور جدید باید حداقل ۸ کاراکتر باشد')
    ])
    confirm_password = PasswordField('تکرار رمز عبور جدید', validators=[
        DataRequired(message='تکرار رمز عبور الزامی است'),
        EqualTo('new_password', message='رمز عبور جدید و تکرار آن باید یکسان باشند')
    ])
    submit = SubmitField('تغییر رمز عبور') 