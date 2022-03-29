from flask import jsonify, Flask, flash, request
from werkzeug.security import check_password_hash, generate_password_hash
from flask_cors import CORS
from db_config import dbMysql
import jwt
from functools import wraps
from uuid import uuid1
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
    print(req_data)
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
def getAdmins(admin_email):
    try:
        mycursor.execute("SELECT id, name, email FROM admin")
        admins = mycursor.fetchall()
        return jsonify({"Message": "List of admins", "admins": admins}), 200
    except Exception as e:
        print(e)
        return jsonify({"Message": "Something Went Wrong"}), 500


@app.route("/certificate", methods=["POST"])
@login_required
def createCertificate(admin_email):
    req_data = request.get_json()
    required_parameters = ["startDate", "endDate", "role", "firstName", "lastName", "email"]
    values = []
    for i in required_parameters:
        if i not in req_data:
            return jsonify({"Message": "Required Feilds Empty"}), 401
        else:
            values.append(req_data[i])

    try:
        id = str(uuid1())
        mycursor.execute("SELECT id FROM admin WHERE email = (%s)", (req_data["email"],))
        phone = None
        if "phone" in req_data:
            phone = req_data["phone"]
        createdBy = mycursor.fetchone()["id"]
        values.extend([id, phone, createdBy])

        mycursor.execute("INSERT INTO certificate(startDate, endDate, role, firstName, lastName, email, id, phone, createdBy) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", values)
        mydb.commit()
        return jsonify({"Message": "Certificate Created"}), 200
    except Exception as e:
        print(e)
        return jsonify({"Message": "Something Went Wrong"}), 500


@app.route("/certificate", methods=["GET"])
@login_required
def getCertificateDetails():
    try:
        mycursor.execute("SELECT * FROM certificate")
        certificates = mycursor.fetchall()
        return jsonify({"Message": "List of certificates", "Certificates": certificates})
    except Exception as e:
        print(e)
        return jsonify({"Message": "Something Went Wrong"}), 500

@app.route("/certificate/<certificate_id>", methods=["GET"])
def getCertificateById(admin_email, certificate_id):
    try:
        certificate_id = certificate_id
        mycursor.execute("SELECT * FROM certificate WHERE id = (%s)", (certificate_id, ))
        certificate = mycursor.fetchone()
        return jsonify({"Message": f"Certificate by id = {certificate_id}", "certificate": certificate})
    except Exception as e:
        print(e)
        return jsonify({"Message": "Something Went Wrong"}), 500


@app.route("/adminCertificate/<admin_id>", methods=["GET"])
@login_required
def getCertificateByAdminId(admin_email, admin_id):
    try:
        admin_id = admin_id
        mycursor.execute("SELECT id FROM admin WHERE email = (%s)", (admin_email,))
        loggedin_admin_id = mycursor.fetchone()["id"]
        print(f"loggedin_admin_id = {loggedin_admin_id}")
        print(f"admin_id = {admin_id}")
        if int(loggedin_admin_id) != int(admin_id):
            return jsonify({"Message": "You do not have access to view certificates"}), 403
        mycursor.execute("SELECT * FROM certificate WHERE createdBy = (%s)", (admin_id,))
        certificates = mycursor.fetchall()
        return jsonify({"Message": f"List of certificates by adminid = {admin_id}", "certificate": certificates})
    except Exception as e:
        print(e)
        return jsonify({"Message": "Something Went Wrong"}), 500


@app.route("/certificate/<certificate_id>", methods=["DELETE"])
@login_required
def deleteCertificate(admin_email, certificate_id):
    try:
        certificate_id = certificate_id
        mycursor.execute("SELECT id FROM admin WHERE email = (%s)", (admin_email,))
        loggedin_admin_id = mycursor.fetchone()["id"]
        mycursor.execute("SELECT * FROM certificate WHERE id = (%s)", (certificate_id,))
        certificate = mycursor.fetchone()
        if int(certificate["createdBy"]) != int(loggedin_admin_id):
            return jsonify({"Message": "You do not have access to delete this certificate"}), 403
        mycursor.execute("DELETE FROM certificate WHERE id = (%s)", (certificate_id,))
        mydb.commit()
        return jsonify({"Message": "Certificate Deleted"})
    except Exception as e:
        print(e)
        return jsonify({"Message": "Something Went Wrong"}), 500
