import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session, redirect
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
from datetime import datetime, timedelta

KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)
load_dotenv()

app.config['SESSION_TYPE'] = 'filesystem' 
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False
app.permanent_session_lifetime = timedelta(days=1)
app.secret_key = KEY
Session(app)

#connect DB
db_host = os.getenv('dbhost')
db_user = os.getenv('dbuser')
db_password = os.getenv('dbpassword')
db_name = os.getenv('dbname')
db_table_name1 = os.getenv('db_table_name1')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    __tablename__ = db_table_name1
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique = True, nullable = False)
    email = db.Column(db.String(250), unique = True, nullable = False)
    password_hash = db.Column(db.String(150), nullable = False)
    created_at = db.Column(db.DateTime, default = datetime.now)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
@app.route('/check_auth', methods=['GET'])
def check_auth():
    print(f"Session in Check:{dict(session)}")
    if 'user_id' in session:
        user = User.query.filter_by(user_id=session['user_id']).first()
        print(session['user_id'])
        session['auth_status'] = True
        if user:
            print(f"User in Check: {user}")
            return jsonify({'auth_status': True,
                            'user_id': session['user_id'],
                            'user_name': session['user_name']
                            }), 200
    print("Current status: Logged out")
    return jsonify({'auth_status' : False, 'error': 'Session not found'}), 200

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    user_name = data.get('user_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    # print(f"password: {password}, confirm_password: {confirm_password}")
    if password != confirm_password:
        print("error passwords do not match")
        return jsonify({"error": "Passwords do not match"}), 400
    
    existing_user = User.query.filter(
        (User.email == email) | (User.user_name == user_name)).first()

    if existing_user:
        print("duplicate users found")
        return jsonify({"error": "User with this email or username already exists"}), 409

    new_user = User(user_name=user_name, email=email, created_at = datetime.now())
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()

        session['auth_status'] = True
        session['user_id'] = new_user.user_id
        session['user_name'] = new_user.user_name
        print('user created')
        print(session)

        return jsonify({"message": "User created successfully",
                        "user_id": session['user_id'],
                        "user_name": session['user_name'],
                        "auth_status": session['auth_status']
                        }), 201
    except Exception as e:
        db.session.rollback()
        print('unexpected error')
        return jsonify({"error": str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        #setting a session
        session['auth_status'] = True
        session['user_id'] = user.user_id
        session['user_name'] = user.user_name
        session['email'] = user.email
        session.permanent = True
        print(f"session data: {session}")
        return jsonify({"message": "Logged in successfully",
                        "user_id": session['user_id'],
                        "user_name": session['user_name'],
                        "auth_status": session['auth_status']
                        }), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401
    
    

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


if __name__ == "__main__":
    app.run(debug=True)
