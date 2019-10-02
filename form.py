from flask import Flask, render_template,request, session, logging, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user, current_user, logout_user


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, ValidationError, SelectField, IntegerField, \
    validators
from wtforms.validators import DataRequired, Length, Email, EqualTo


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=20)])
    roll = StringField('Roll',
                       validators=[DataRequired(), Length(min=2, max=9)])
    dept = StringField('Department', validators=[DataRequired()])
    section = StringField('Section', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_roll(self, roll):
        user = Register.query.filter_by(roll=roll.data).first()
        if user:
            raise ValidationError('Roll number already registered try with another one')

    def validate_name(self, name):
        user = Register.query.filter_by(name=name.data).first()
        if user:
            raise ValidationError('Name alreasy registered try with another one')


class LoginForm(FlaskForm):
    roll = StringField('Roll', validators=[DataRequired(), Length(min=2, max=9)])
    password = PasswordField('password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

    submit = SubmitField('Login')

class StatsForm(FlaskForm):
    accept=SubmitField()
    decline=SubmitField()

class selectForm(FlaskForm):
    roomate_roll = StringField('Roll', validators=[DataRequired()])
    submit = SubmitField('Send Request')

    def validate_roomate_roll(self, roomate_roll):
        users = Roomate.query.filter_by(user=current_user.roll).all()
        for user in users:
            if user and user.roomate == roomate_roll.data:
                raise ValidationError('Request already sent try with another guy')


app = Flask(__name__)

app.config['SECRET_KEY'] = 'd920f6b3344d951bac44049af03f60f2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/hostel'
db = SQLAlchemy(app)

login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return Register.query.get(int(user_id))


class Register(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    roll = db.Column(db.String(20), unique=True, nullable=False)
    dept = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)


class Roomate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), unique=False,nullable=False)
    roomate = db.Column(db.String(100), unique=False,nullable=False)
    status=db.Column(db.Integer,nullable=True)

@app.route("/")
def index():
    return render_template("home.html")


@app.route("/Hostelallotment")
def hostelallotment():
    print('hello')
    return render_template("home.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/sentrequest")
def sentrequest():
    prem=[]
    sauravs = Roomate.query.filter_by(user=current_user.roll).all()
    saurav = Roomate.query.filter_by(user=current_user.roll).first()
    for saurav in sauravs:
        q=Register.query.filter_by(roll=saurav.roomate).first()
        prem+=[q.name]
    return render_template("sentrequest.html", sauravs=sauravs, saurav=saurav,len=len(sauravs),prem=prem)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('hostelallotment'))
    form = RegistrationForm()
    if form.validate_on_submit():
        password = form.password.data
        user = Register(name=form.name.data, roll=form.roll.data, dept=form.dept.data, section=form.section.data,
                        password=password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.name.data}!! Now you can login', 'sucess')
        return redirect(url_for('signin'))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('hostelallotment'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Register.query.filter_by(roll=form.roll.data).first()
        if user and user.password == form.password.data:
            login_user(user, remember=form.remember.data)
            return redirect(url_for('hostelallotment'))
        else:
            flash('login unsuccessfull', 'danger')
    return render_template("signin.html", form=form)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    form=StatsForm()

    select_form = selectForm()
    if select_form.validate_on_submit():
        us = Register.query.filter_by(roll=select_form.roomate_roll.data).first()
        if us:
            roomateroll = select_form.roomate_roll.data
            room = Roomate(user=current_user.roll, roomate=roomateroll,status=0)
            db.session.add(room)
            db.session.commit()
            flash(f'Request has been made successfully for roomate', 'sucess')
            return render_template("dashboard.html", select_form=select_form)
        else:
            flash(f'{select_form.roomate_roll.data} is not registered try with another guy', 'danger')
            return render_template("dashboard.html", select_form=select_form)
    ser=Roomate.query.filter_by(roomate=current_user.roll).first()
    sers=Roomate.query.filter_by(roomate=current_user.roll).all()
    return render_template("dashboard.html", select_form=select_form, form=form, ser=ser,sers=sers)




@app.route("/request", methods=["GET", "POST"])
def raj():
    form = LoginForm()
    ser = Roomate.query.filter_by(roomate=current_user.roll).first()
    sers = Roomate.query.filter_by(roomate=current_user.roll).all()
    if request.method=="POST":
        for ser in sers:

            if request.form["submit_button"]=="accept":
                ser.status=1
                db.session.commit()
    return redirect(url_for('hostelallotment'))

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('hostelallotment'))


if __name__ == '__main__':
    app.run(debug=True)
