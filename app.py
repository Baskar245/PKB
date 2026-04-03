from flask import Flask, render_template, request, redirect, session, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "zip", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
MONGO_URL = "mongodb+srv://baskar2711:baskar@cluster0.9p8nb9h.mongodb.net/"
client = MongoClient(MONGO_URL)
db = client["pkb"]
collection = db["requests"]

# ---------------- ADMIN ----------------
ADMIN_USER = "baskar"
ADMIN_PASS = "7654"

# ---------------- FILE CHECK ----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- SUBMIT ----------------
@app.route("/submit", methods=["POST"])
def submit():
    data = request.form.to_dict()

    # Handle "Other"
    if data.get("service") == "Other":
        data["service"] = data.get("other_service")

    data["status"] = "pending"

    # File upload
    file = request.files.get("file")
    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        data["file"] = filename
    else:
        data["file"] = None

    collection.insert_one(data)

    return "<h2>✅ Request Sent Successfully!</h2><a href='/'>Go Back</a>"

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")
        else:
            return "❌ Invalid Login"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    data = list(collection.find())

    total_requests = len(data)
    total_income = sum(
        int(d.get("budget", 0))
        for d in data
        if d.get("status") == "completed"
    )

    return render_template("dashboard.html",
                           data=data,
                           total_requests=total_requests,
                           total_income=total_income)

# ---------------- DOWNLOAD FILE ----------------
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ---------------- UPDATE STATUS ----------------
@app.route("/update/<id>/<status>")
def update(id, status):
    if not session.get("admin"):
        return redirect("/admin")

    collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": status}}
    )

    return redirect("/dashboard")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)