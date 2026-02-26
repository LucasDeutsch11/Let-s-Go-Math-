from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin
try:
    cred = credentials.Certificate("ServiceAccountKey.json")
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase initialization failed: {e}")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

PROBLEMS = [
    {"instruction" : "Solve for", "variable" : "x", "equation" : "x + 5 = 7", "answer" : 2},
    {"instruction" : "Solve for", "variable" : "x", "equation" : "x + 9 = 15", "answer" : 6},
    {"instruction" : "Solve for", "variable" : "x", "equation" : "x - 4 = 10", "answer" : 14},
    {"instruction" : "Solve for", "variable" : "x", "equation" : "2x = 12",    "answer" : 6},
    {"instruction" : "Solve for", "variable" : "x", "equation" : "3x + 1 = 10","answer" : 3},
]

@app.route("/", methods=["GET"])
def home():
    user_info = None
    if "user_id" in session:
        user_info = {
            "email": session.get("user_email"),
            "name": session.get("user_name", "User")
        }
    return render_template("home.html", user=user_info)

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/signup", methods=["GET"])
def signup():
    return render_template("signup.html")

@app.route("/reset-password", methods=["GET"])
def reset_password():
    return render_template("reset_password.html")

@app.route("/api/sessionLogin", methods=["POST"])
def session_login():
    try:
        id_token = request.json.get("idToken")
        decoded_token = auth.verify_id_token(id_token)
        session["user_id"] = decoded_token["uid"]
        session["user_email"] = decoded_token.get("email")
        session["user_name"] = decoded_token.get("name", decoded_token.get("email", "User"))
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
@app.route("/start", methods=["GET"])
def start():
    session["problem_index"] = 0
    return redirect(url_for("practice"))

@app.route("/practice", methods=["GET", "POST"])
def practice():
    idx = session.get("problem_index", 0)
    if idx < 0 or idx >= len(PROBLEMS):
        idx = 0
        session["problem_index"] = 0
    problem = PROBLEMS[idx]

    feedback = None
    user_answer = ""
    
    if request.method == "POST" :
        user_answer = request.form.get("answer", "").strip()

        if user_answer == "":
            feedback = "Please enter an answer."
        else:
            try:
                user_num = int(user_answer)
                if user_num == problem["answer"] :
                    feedback = "Correct!"
                else:
                    feedback = "Incorrect!"
            except ValueError:
                feedback = "Please enter a valid whole number."

    return render_template(
        "index.html", 
        instruction=problem["instruction"], 
        variable=problem["variable"],
        equation=problem["equation"],
        feedback=feedback, 
        user_answer=user_answer,
        problem_number=idx+1,
        total_problems=len(PROBLEMS)
    )

@app.route("/next", methods=["POST"])
def next_problem():
    idx = session.get("problem_index", 0)
    idx = (idx + 1) % len(PROBLEMS)
    session["problem_index"] = idx
    return redirect(url_for("practice"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)