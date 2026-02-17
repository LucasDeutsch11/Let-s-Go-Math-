from flask import Flask, render_template, request, redirect, url_for, session
import os

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
    return render_template("home.html")
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