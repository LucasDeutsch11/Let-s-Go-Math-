from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin (optional for production)
firebase_available = False
try:
    # Simple initialization without signal timeout (Render-compatible)
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    firebase_available = True
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization failed (running without auth): {e}")
    firebase_available = False

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

MATH_TOPICS = {
    "linear_equations": {
        "title": "Linear Equations",
        "description": "Solve simple linear equations with one variable",
        "problems": [
            {"instruction": "Solve for", "variable": "x", "equation": "x + 5 = 7", "answer": 2},
            {"instruction": "Solve for", "variable": "x", "equation": "x + 9 = 15", "answer": 6},
            {"instruction": "Solve for", "variable": "x", "equation": "x - 4 = 10", "answer": 14},
            {"instruction": "Solve for", "variable": "x", "equation": "2x = 12", "answer": 6},
            {"instruction": "Solve for", "variable": "x", "equation": "3x + 1 = 10", "answer": 3},
        ]
    },
    "inequalities": {
        "title": "Inequalities",
        "description": "Solve and graph linear inequalities",
        "problems": [
            {"instruction": "Solve for", "variable": "x", "equation": "x + 3 > 8", "answer": 5},
            {"instruction": "Solve for", "variable": "x", "equation": "2x ≤ 10", "answer": 5},
            {"instruction": "Solve for", "variable": "x", "equation": "x - 7 < 2", "answer": 9},
            {"instruction": "Solve for", "variable": "x", "equation": "3x ≥ 15", "answer": 5},
            {"instruction": "Solve for", "variable": "x", "equation": "x/2 > 4", "answer": 8},
        ]
    },
    "systems": {
        "title": "Systems of Equations",
        "description": "Solve systems of linear equations - answer in (x,y) format",
        "problems": [
            {"instruction": "Solve for x and y", "variable": "(x,y)", "equation": "x + y = 7, x - y = 1", "answer": "(4,3)"},
            {"instruction": "Solve for x and y", "variable": "(x,y)", "equation": "2x + y = 10, x - y = 2", "answer": "(4,2)"},
            {"instruction": "Solve for x and y", "variable": "(x,y)", "equation": "x + 2y = 8, x = 2", "answer": "(2,3)"},
            {"instruction": "Solve for x and y", "variable": "(x,y)", "equation": "3x + y = 11, y = 2", "answer": "(3,2)"},
            {"instruction": "Solve for x and y", "variable": "(x,y)", "equation": "x + y = 5, 2x - y = 1", "answer": "(2,3)"},
        ]
    },
    "exponents": {
        "title": "Exponents",
        "description": "Work with exponential expressions and rules",
        "problems": [
            {"instruction": "Simplify", "variable": "", "equation": "2³", "answer": 8},
            {"instruction": "Simplify", "variable": "", "equation": "5²", "answer": 25},
            {"instruction": "Solve for", "variable": "x", "equation": "x² = 16", "answer": 4},
            {"instruction": "Simplify", "variable": "", "equation": "3⁴", "answer": 81},
            {"instruction": "Solve for", "variable": "x", "equation": "2^x = 8", "answer": 3},
        ]
    },
    "polynomials": {
        "title": "Polynomials",
        "description": "Add, subtract, and multiply polynomials",
        "problems": [
            {"instruction": "Simplify", "variable": "", "equation": "(x + 3) + (2x + 1)", "answer": "3x + 4"},
            {"instruction": "Expand", "variable": "", "equation": "2(x + 5)", "answer": "2x + 10"},
            {"instruction": "Simplify", "variable": "", "equation": "(3x + 2) - (x + 1)", "answer": "2x + 1"},
            {"instruction": "Expand", "variable": "", "equation": "3(2x - 4)", "answer": "6x - 12"},
            {"instruction": "Simplify", "variable": "", "equation": "2x² + 3x² - x²", "answer": "4x²"},
        ]
    },
    "factoring": {
        "title": "Factoring",
        "description": "Factor quadratic expressions and polynomials",
        "problems": [
            {"instruction": "Factor", "variable": "", "equation": "x² - 5x + 6", "answer": "(x-2)(x-3)"},
            {"instruction": "Factor", "variable": "", "equation": "x² + 7x + 12", "answer": "(x+3)(x+4)"},
            {"instruction": "Factor", "variable": "", "equation": "2x + 6", "answer": "2(x+3)"},
            {"instruction": "Factor", "variable": "", "equation": "x² - 9", "answer": "(x+3)(x-3)"},
            {"instruction": "Factor", "variable": "", "equation": "x² + 6x + 9", "answer": "(x+3)²"},
        ]
    },
    "quadratics": {
        "title": "Quadratic Equations",
        "description": "Solve quadratic equations - list all solutions separated by commas",
        "problems": [
            {"instruction": "Solve for", "variable": "x", "equation": "x² - 4 = 0", "answer": "-2,2"},
            {"instruction": "Solve for", "variable": "x", "equation": "x² + 2x - 3 = 0", "answer": "-3,1"},
            {"instruction": "Solve for", "variable": "x", "equation": "(x - 1)² = 4", "answer": "-1,3"},
            {"instruction": "Solve for", "variable": "x", "equation": "x² - 6x + 8 = 0", "answer": "2,4"},
            {"instruction": "Solve for", "variable": "x", "equation": "2x² - 8 = 0", "answer": "-2,2"},
        ]
    },
    "word_problems": {
        "title": "Word Problems",
        "description": "Apply algebra to real-world situations",
        "problems": [
            {"instruction": "Solve for", "variable": "x", "equation": "A number plus 7 equals 15. Find the number.", "answer": 8},
            {"instruction": "Solve for", "variable": "x", "equation": "Twice a number is 18. Find the number.", "answer": 9},
            {"instruction": "Solve for", "variable": "x", "equation": "A number minus 5 equals 12. Find the number.", "answer": 17},
            {"instruction": "Solve for", "variable": "x", "equation": "Three times a number plus 4 equals 19. Find the number.", "answer": 5},
            {"instruction": "Solve for", "variable": "x", "equation": "Half of a number is 6. Find the number.", "answer": 12},
        ]
    }
}

@app.route("/", methods=["GET"])
def home():
    user_info = None
    if "user_id" in session:
        user_info = {
            "email": session.get("user_email"),
            "name": session.get("user_name", "User")
        }
    return render_template("home.html", user=user_info)

@app.route("/topics")
def topics():
    user_info = None
    user_progress = {}
    
    if "user_id" in session:
        user_info = {
            "email": session.get("user_email"),
            "name": session.get("user_name", "User")
        }
        # Get user progress from session (in a real app, this would be from database)
        user_progress = session.get("progress", {})
        
        # Calculate percentages for each topic
        for topic_id in user_progress:
            if user_progress[topic_id]["total"] > 0:
                user_progress[topic_id]["percentage"] = int((user_progress[topic_id]["completed"] / user_progress[topic_id]["total"]) * 100)
            else:
                user_progress[topic_id]["percentage"] = 0
    
    return render_template("topics.html", user=user_info, topics=MATH_TOPICS, progress=user_progress)

@app.route("/topic/<topic_id>")
def topic_detail(topic_id):
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    user_info = None
    user_progress = {}
    
    if "user_id" in session:
        user_info = {
            "email": session.get("user_email"),
            "name": session.get("user_name", "User")
        }
        user_progress = session.get("progress", {})
    
    topic = MATH_TOPICS[topic_id]
    topic_progress = user_progress.get(topic_id, {"completed": 0, "total": len(topic["problems"])})
    
    # Calculate progress percentage for CSS
    if topic_progress["total"] > 0:
        topic_progress["percentage"] = int((topic_progress["completed"] / topic_progress["total"]) * 100)
    else:
        topic_progress["percentage"] = 0
    
    return render_template("topic_detail.html", 
                         user=user_info, 
                         topic=topic, 
                         topic_id=topic_id,
                         progress=topic_progress)

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
    if not firebase_available:
        return jsonify({"error": "Authentication not available"}), 503
    try:
        data = request.get_json()
        if not data or "idToken" not in data:
            return jsonify({"error": "No ID token provided"}), 400
            
        id_token = data.get("idToken")
        print(f"Attempting to verify ID token for session login")
        
        decoded_token = auth.verify_id_token(id_token)
        print(f"Token verified for user: {decoded_token.get('email')}")
        
        session["user_id"] = decoded_token["uid"]
        session["user_email"] = decoded_token.get("email")
        session["user_name"] = decoded_token.get("name", decoded_token.get("email", "User"))
        
        print(f"Session created for user: {session['user_email']}")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Session login error: {str(e)}")
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
@app.route("/start")
@app.route("/start/<topic_id>")
def start(topic_id=None):
    if topic_id and topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    # Default to linear equations if no topic specified
    if not topic_id:
        topic_id = "linear_equations"
    
    session["current_topic"] = topic_id
    session["problem_index"] = 0
    return redirect(url_for("practice"))

@app.route("/practice", methods=["GET", "POST"])
def practice():
    topic_id = session.get("current_topic", "linear_equations")
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    topic = MATH_TOPICS[topic_id]
    problems = topic["problems"]
    
    idx = session.get("problem_index", 0)
    if idx < 0 or idx >= len(problems):
        idx = 0
        session["problem_index"] = 0
    
    problem = problems[idx]
    feedback = None
    user_answer = ""
    
    if request.method == "POST":
        user_answer = request.form.get("answer", "").strip()

        if user_answer == "":
            feedback = "Please enter an answer."
        else:
            try:
                # Handle different answer types
                if isinstance(problem["answer"], str):
                    # For algebraic expressions and coordinate pairs, normalize whitespace
                    user_answer_clean = user_answer.replace(" ", "")
                    correct_answer_clean = str(problem["answer"]).replace(" ", "")
                    
                    # Check if this is a comma-separated answer (like quadratic solutions)
                    if "," in correct_answer_clean and "," in user_answer_clean:
                        # Parse both answers as comma-separated values
                        user_values = set(user_answer_clean.split(","))
                        correct_values = set(correct_answer_clean.split(","))
                        is_correct = user_values == correct_values
                    # Check if this is a factored expression (contains parentheses with multiplication)
                    elif "(" in correct_answer_clean and ")" in correct_answer_clean and "(" in user_answer_clean and ")" in user_answer_clean:
                        # Extract factors from both answers
                        import re
                        # Find all parenthetical expressions
                        correct_factors = re.findall(r'\([^)]+\)', correct_answer_clean)
                        user_factors = re.findall(r'\([^)]+\)', user_answer_clean)
                        
                        # Convert to sets to ignore order
                        correct_factors_set = set(correct_factors)
                        user_factors_set = set(user_factors)
                        
                        # Check if the sets match (ignoring order)
                        is_correct = correct_factors_set == user_factors_set
                    else:
                        # Regular string comparison for other answer types
                        is_correct = user_answer_clean.lower() == correct_answer_clean.lower()
                    
                    if is_correct:
                        feedback = "Correct!"
                        # Update progress for logged-in users
                        if "user_id" in session:
                            try:
                                update_user_progress(topic_id, idx)
                            except Exception as e:
                                print(f"Progress update error: {e}")
                    else:
                        feedback = "Incorrect!"
                else:
                    # For numeric answers, try to convert to int
                    try:
                        user_num = int(user_answer)
                        if user_num == problem["answer"]:
                            feedback = "Correct!"
                            # Update progress for logged-in users
                            if "user_id" in session:
                                try:
                                    update_user_progress(topic_id, idx)
                                except Exception as e:
                                    print(f"Progress update error: {e}")
                        else:
                            feedback = "Incorrect!"
                    except ValueError:
                        feedback = "Please enter a valid number."
            except Exception as e:
                print(f"Answer checking error: {e}")
                feedback = "An error occurred. Please try again."

    return render_template(
        "practice.html", 
        topic=topic,
        topic_id=topic_id,
        instruction=problem["instruction"], 
        variable=problem["variable"],
        equation=problem["equation"],
        feedback=feedback, 
        user_answer=user_answer,
        problem_number=idx+1,
        total_problems=len(problems)
    )

def update_user_progress(topic_id, problem_index):
    """Update user progress for a specific topic"""
    if "progress" not in session:
        session["progress"] = {}
    
    if topic_id not in session["progress"]:
        session["progress"][topic_id] = {
            "completed": 0,
            "total": len(MATH_TOPICS[topic_id]["problems"]),
            "solved_problems": []
        }
    
    # Ensure solved_problems is a list
    if not isinstance(session["progress"][topic_id]["solved_problems"], list):
        session["progress"][topic_id]["solved_problems"] = []
    
    # Add this problem to solved problems if not already solved
    if problem_index not in session["progress"][topic_id]["solved_problems"]:
        session["progress"][topic_id]["solved_problems"].append(problem_index)
    
    # Update completed count
    session["progress"][topic_id]["completed"] = len(session["progress"][topic_id]["solved_problems"])
    session.modified = True

@app.route("/next", methods=["POST"])
def next_problem():
    topic_id = session.get("current_topic", "linear_equations")
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    topic = MATH_TOPICS[topic_id]
    idx = session.get("problem_index", 0)
    idx += 1
    
    # Check if all problems in this topic are completed
    if idx >= len(topic["problems"]):
        return redirect(url_for("topic_completed", topic_id=topic_id))
    
    session["problem_index"] = idx
    return redirect(url_for("practice"))

@app.route("/completed/<topic_id>")
def topic_completed(topic_id):
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    topic = MATH_TOPICS[topic_id]
    user_info = None
    
    if "user_id" in session:
        user_info = {
            "email": session.get("user_email"),
            "name": session.get("user_name", "User")
        }
    
    return render_template("topic_completed.html", user=user_info, topic=topic, topic_id=topic_id)

@app.route("/health")
def health_check():
    """Simple health check for monitoring"""
    return {"status": "healthy", "firebase": firebase_available}, 200

@app.route("/restart/<topic_id>", methods=["POST"])
def restart_topic(topic_id):
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    session["current_topic"] = topic_id
    session["problem_index"] = 0
    return redirect(url_for("practice"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Use debug=False in production for better performance
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)