from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

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