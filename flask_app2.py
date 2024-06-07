from flask import Flask, render_template, url_for, session, redirect, request, flash
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
from flask_migrate import Migrate
import numpy as np
import pandas as pd
import datetime as dt
import random

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.secret_key = 'secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    __tablename__ = 'users_table'
    _id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    electric_meter_id = db.Column(db.Integer, nullable=False)
    water_meter_id = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(100), nullable=False)

    def __init__(self, email, password, username, customer_id, address, electric_meter_id, water_meter_id, fullname):
        self.email = email
        self.password = generate_password_hash(password)
        self.username = username
        self.customer_id = customer_id
        self.electric_meter_id = electric_meter_id
        self.water_meter_id = water_meter_id
        self.address = address
        self.fullname = fullname

class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    limit = db.Column(db.String, default=1000)
    user_id = db.Column(db.Integer, db.ForeignKey('users_table._id'))

    def __init__(self, name, user_id, limit=1000):
        self.name = name
        self.limit = limit
        self.user_id = user_id

def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)

@app.route("/", methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not email:
            flash('Masukkan email anda')
            return redirect(url_for('home'))
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['email'] = email
            flash("login successful", "info")
            return redirect(url_for('dashboard'))
        else:
            flash('invalid username or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        customer_id = request.form['customer_id']
        electric_meter_id = request.form['electric_meter_id']
        water_meter_id = request.form['water_meter_id']
        address = request.form['address']
        fullname = request.form['fullname']
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('email already exists', 'error')
            return redirect(url_for('signup'))

        new_user = User(username=username, email=email, password=password, customer_id=customer_id,
                        electric_meter_id=electric_meter_id, water_meter_id=water_meter_id, address=address, fullname=fullname)
        db.session.add(new_user)
        db.session.commit()
        session['email'] = email
        flash('Account saved')
        return render_template('login.html')
    else:
        return render_template('signup_gmail.html')

@app.route("/logout", methods=['POST', 'GET'])
def logout_2():
    if request.method == 'POST':
        session.pop('email', None)
        flash("You're logged out", 'info')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route("/dashboard", methods=['POST', 'GET'])
def dashboard():
    if 'email' in session:
        email = session['email']
        user = User.query.filter_by(email=email).first()
        if user:
            username = user.username
            return render_template('dashboard.html', username=username, electricity_usage=random.randint(100, 2200), water_usage=random.randint(50, 1000))
    return redirect(url_for('home'))

@app.route('/perangkat_terhubung', methods=['GET', 'POST'])
def perangkat_terhubung():
    devices = Device.query.all()
    return render_template('perangkat_terhubung.html', devices=devices)

@app.route('/add_device', methods=['POST'])
def add_device():
    name = request.form['name']
    limit = request.form['limit']
    user_id = 1 
    new_device = Device(name=name, user_id=user_id, limit=limit)
    db.session.add(new_device)
    db.session.commit()
    return redirect(url_for('perangkat_terhubung'))

@app.route('/analisis_listrik')
def analisis_listrik():
    labelsElectricity = pd.date_range(start='2024-05-01', periods=30, freq='D') 
    dataElectricity = np.random.randint(70, 220, 30).tolist()
    labels_7Electricity = labelsElectricity[-7:].strftime('%Y-%m-%d').tolist()
    data_7Electricity = dataElectricity[-7:]
    totalElectricityCost7 = np.sum(data_7Electricity) * 1700
    averageElectricityUsage7 = round(np.mean(data_7Electricity), 2)

    labels_30Electricity = labelsElectricity.strftime('%Y-%m-%d').tolist()
    data_30Electricity = dataElectricity
    totalElectricityCost30 = np.sum(data_30Electricity) * 1700
    averageElectricityUsage30 = round(np.mean(data_30Electricity), 2)

    return render_template(
       'analisis_listrik.html',
       labels_7Electricity=labels_7Electricity,
       labels_30Electricity=labels_30Electricity,
       data_7Electricity=data_7Electricity,
       data_30Electricity=data_30Electricity,
       totalElectricityCost30=totalElectricityCost30,
       totalElectricityCost7=totalElectricityCost7,
       averageElectricityUsage7=averageElectricityUsage7,
       averageElectricityUsage30=averageElectricityUsage30,
    )

@app.route('/analisis_air')
def analisis_air():
    labels = pd.date_range(start='2024-05-01', periods=30, freq='D')
    data = np.random.randint(100, 270, 30).tolist()
    labels_7 = labels[-7:].strftime('%Y-%m-%d').tolist()
    data_7 = data[-7:]
    total_water_cost_7 = sum(data_7) * 3440
    average_usage_7 = round(np.mean(data_7), 2)
    
    labels_30 = labels.strftime('%Y-%m-%d').tolist()
    data_30 = data
    total_water_cost_30 = sum(data_30) * 3440
    average_usage_30 = round(np.mean(data_30), 2)

    return render_template(
        'analisis_air.html',
        labels_7=labels_7,
        labels_30=labels_30,
        data_7=data_7,
        data_30=data_30,
        total_water_cost_7=total_water_cost_7,
        average_usage_7=average_usage_7,
        total_water_cost_30=total_water_cost_30,
        average_usage_30=average_usage_30
    )

@app.route("/identity")
def identity():
    email = session['email']
    user = User.query.filter_by(email=email).first()

    if user:
        username = user.username
        email = user.email
        customer_id = user.customer_id
        electric_meter_id = user.electric_meter_id
        water_meter_id = user.water_meter_id
        address = user.address
        fullname = user.fullname
        electricity_usage = random.randint(100, 2200)
        water_usage = random.randint(50, 1000)
        electricity_cost = 1444.70 * electricity_usage
        water_cost = 3440 * water_usage
        electricity_status = "Normal" if electricity_usage <= 500 else "High"
        water_status = "Normal" if water_usage <= 300 else "High"
        return render_template('identity.html', username=username, email=email, customer_id=customer_id, electricity_cost=electricity_cost, electricity_usage=electricity_usage, electricity_status=electricity_status, water_cost=water_cost, water_status=water_status, water_usage=water_usage, address=address, electric_meter_id=electric_meter_id, water_meter_id=water_meter_id, fullname=fullname)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
