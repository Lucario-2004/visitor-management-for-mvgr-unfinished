from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
from base64 import b64encode
from io import BytesIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visitor.db'

db = SQLAlchemy(app)

class SecurityGuard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Administrator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    purpose = db.Column(db.String(100), nullable=False)
    in_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    out_time = db.Column(db.DateTime, nullable=True)
    qr_code = db.Column(db.String(200), nullable=False)

    @property
    def qr_code_image(self):
        if self.qr_code:
            img_data = BytesIO(qrcode.make(f'{self.name},{self.phone},{self.purpose}'))
            img_data.seek(0)
            return b64encode(img_data.read()).decode()
        else:
            return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = SecurityGuard.query.filter_by(username=username).first()
        if user and user.password == password:
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = SecurityGuard(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    visitors = Visitor.query.all()
    return render_template('dashboard.html', visitors=visitors)

@app.route('/add_visitor', methods=['GET', 'POST'])
def add_visitor():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        purpose = request.form['purpose']
        qr_code = qrcode.make(f'{name},{phone},{purpose}')
        buffer = BytesIO()
        qr_code.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_data = b64encode(buffer.read()).decode()
        visitor = Visitor(name=name, phone=phone, purpose=purpose, qr_code=qr_code_data)
        db.session.add(visitor)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_visitor.html')

@app.route('/update_visitor/<int:id>', methods=['GET', 'POST'])
def update_visitor(id):
    visitor = Visitor.query.get_or_404(id)
    if request.method == 'POST':
        visitor.out_time = datetime.strptime(request.form['out_time'], '%Y-%m-%dT%H:%M')
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('update_visitor.html', visitor=visitor)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)