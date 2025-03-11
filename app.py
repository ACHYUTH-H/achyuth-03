from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import openai
from models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

openai.api_key = 'your_openai_api_key'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_response(query):
    response = openai.Completion.create(
        engine="gpt-4",
        prompt=query,
        max_tokens=150
    )
    return response.choices[0].text.strip()

@app.route('/')
def index():
    return app.send_static_file('build/index.html')

@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('static'):
        return app.send_static_file(path)
    return app.send_static_file('build/index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.json['query']
    answer = get_response(query)
    return jsonify(answer)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    new_user = User(name=data['name'], email=data['email'], age=data['age'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user is None or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    login_user(user)
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/secure-data', methods=['GET'])
@login_required
def secure_data():
    return jsonify({'data': 'This is secured data accessible only to authenticated users'}), 200

if __name__ == "__main__":
    app.run(debug=True)
