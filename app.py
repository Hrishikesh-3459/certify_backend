import json
from flask import jsonify, Flask, flash, request
from werkzeug.security import check_password_hash, generate_password_hash
from flask_cors import CORS
from db_config import dbMysql
import jwt
from functools import wraps
import os
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")

db = dbMysql()
mydb = db.connection()
mycursor = mydb.cursor(buffered=True, dictionary=True)
db.configure_db(mycursor)

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    # adding the cors header property manually
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    return response

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]
        if not token:
            
            return jsonify({"Message" : "Auth Failed"}), 401
  
        try:
            data = jwt.decode(jwt=token, key=JWT_SECRET, algorithms="HS256")
            current_user = data["email"]
        except Exception as e:
            print(e)
            return jsonify({"Message" : "Auth Failed"}), 401

        return  f(current_user, *args, **kwargs)
  
    return decorated

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "hello ji"})

@app.route("/register", methods=["POST"])
def register():
    req_data = request.get_json()
    try:
        email = req_data["email"]
        password = req_data["password"]
        name = req_data["name"]
    except KeyError:
        return jsonify({"Message": "Required Feilds Empty"}), 401

    try:
        mycursor.execute("SELECT email FROM admin WHERE email = (%s)", (email,))
        row = mycursor.fetchone()
        if row:
            return jsonify({"Message": "User Already Exists"})
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        mycursor.execute("INSERT INTO admin(name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        mydb.commit()
        return jsonify({"Message": "Admin Created"}), 200
    except Exception as e:
        return jsonify({"Message": "Something Went Wrong", "Error": e}), 500
        

@app.route("/login", methods=["POST"])
def login():
    req_data = request.get_json()
    try:
        email = req_data["email"]
        password = req_data["password"]
    except KeyError:
        return jsonify({"Message": "Required Feilds Empty"}), 401
    try:
        mycursor.execute("SELECT email, password FROM admin WHERE email = (%s)", (email,))
        row = mycursor.fetchone()

        if not row:
            return jsonify({"Message": "User Not Found"})
        if not check_password_hash(row["password"], password):
            return jsonify({"Message": "Incorrect Password"}), 401

        payload_data = {"email": email}
        token = jwt.encode(payload = payload_data, key = JWT_SECRET, algorithm="HS256")
        return jsonify({"Message": "Login Successful", "token": token}), 200
    except Exception as e:
        return jsonify({"Message": "Something Went Wrong", "Error": e}), 500

@app.route("/admin", methods=["GET"])
@login_required  
def getAdmins(user_email):
    try:
        mycursor.execute("SELECT id, name, email FROM admin")
        admins = mycursor.fetchall()
        return jsonify({"Message": "List of admins", "admins": admins}), 200
    except Exception as e:
        return jsonify({"Message": "Something Went Wrong", "Error": e}), 500
