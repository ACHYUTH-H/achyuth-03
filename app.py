from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import openai
from models import db, User
import requests

app = Flask(__name__, static_folder='frontend/my-app/build', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/dbname'
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
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('static'):
        return app.send_static_file(path)
    return app.send_static_file('index.html')

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

@app.route('/loan-eligibility', methods=['POST'])
def loan_eligibility():
    data = request.get_json()
    # Logic to fetch loan eligibility from banking API
    response = requests.post('https://bankingapi.com/eligibility', json=data)
    return jsonify(response.json())

@app.route('/financial-tips', methods=['GET'])
def financial_tips():
    # Logic to fetch financial tips
    tips = ["Save regularly", "Invest wisely", "Track your expenses"]
    return jsonify({'tips': tips})

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    query = data['query']
    target_language = data['target_language']
    response = requests.post('https://translation.googleapis.com/language/translate/v2', params={
        'q': query,
        'target': target_language,
        'key': 'your_google_translate_api_key'
    })
    return jsonify(response.json()['data']['translations'][0]['translatedText'])

if __name__ == "__main__":
    app.run(debug=True)
