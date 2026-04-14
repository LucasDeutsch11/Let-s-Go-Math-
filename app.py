from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import time
import random
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime, timezone

# Initialize Firebase Admin (optional for production)
firebase_available = False
db = None
try:
    # Simple initialization without signal timeout (Render-compatible)
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    firebase_available = True
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization failed (running without auth): {e}")
    firebase_available = False

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# Challenge Mode Configuration
CHALLENGE_CONFIG = {
    "rounds": 3,
    "questions_per_round": 3,
    "time_limit_seconds": 90,  # 1 minute 30 seconds per round
    "points": {
        "correct_answer": 11,   # 11 points base × 9 questions = 99 points
        "speed_bonus_max": 1,   # Up to 1 bonus point per question (total max: 100)
        "round_multipliers": [1, 1, 1]  # No multipliers - keep it simple and fair
    }
}

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
            {"instruction": "Solve for", "variable": "x", "equation": "x + 3 > 8", "answer": "x > 5"},
            {"instruction": "Solve for", "variable": "x", "equation": "2x ≤ 10", "answer": "x ≤ 5"},
            {"instruction": "Solve for", "variable": "x", "equation": "x - 7 < 2", "answer": "x < 9"},
            {"instruction": "Solve for", "variable": "x", "equation": "3x ≥ 15", "answer": "x ≥ 5"},
            {"instruction": "Solve for", "variable": "x", "equation": "x/2 > 4", "answer": "x > 8"},
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
            {"instruction": "Solve for", "variable": "x", "equation": "x² = 16", "answer": "-4,4"},
            {"instruction": "Simplify", "variable": "", "equation": "3⁴", "answer": 81},
            {"instruction": "Solve for", "variable": "x", "equation": "2ˣ = 8", "answer": 3},
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
            {"instruction": "Solve for", "variable": "x", "equation": "A number plus 7 equals 15." , "answer": 8},
            {"instruction": "Solve for", "variable": "x", "equation": "Twice a number is 18." , "answer": 9},
            {"instruction": "Solve for", "variable": "x", "equation": "A number minus 5 equals 12." , "answer": 17},
            {"instruction": "Solve for", "variable": "x", "equation": "Three times a number plus 4 equals 19." , "answer": 5},
            {"instruction": "Solve for", "variable": "x", "equation": "Half of a number is 6." , "answer": 12},
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
    return render_template("home_screen.html", user=user_info)

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
    
    return render_template("topics_screen.html", user=user_info, topics=MATH_TOPICS, progress=user_progress)

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
    return render_template("login_screen.html")

@app.route("/signup", methods=["GET"])
def signup():
    return render_template("signup_screen.html")

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
    # Gather progress from Firestore if logged in, else session
    progress = {}
    session_progress = session.get("progress", {})
    if firebase_available and "user_id" in session:
        try:
            doc = db.collection("user_progress").document(session["user_id"]).get()
            if doc.exists:
                firestore_progress = doc.to_dict().get("progress", {})
                session_progress = firestore_progress
        except Exception as e:
            print(f"Error loading progress from Firestore: {e}")
    for topic_id, data in session_progress.items():
        topic_info = MATH_TOPICS.get(topic_id, {"title": topic_id})
        progress[topic_id] = {
            "title": topic_info["title"],
            "completed": data.get("completed", 0),
            "total": data.get("total", len(topic_info.get("problems", [])))
        }
    return render_template("dashboard.html", progress=progress)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
@app.route("/start", methods=["GET"])
@app.route("/start/<topic_id>", methods=["GET"])
def start(topic_id=None):
    # Get difficulty from query string (default: easy)
    difficulty = request.args.get("difficulty", "easy")
    if topic_id and topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    # Default to linear equations if no topic specified
    if not topic_id:
        topic_id = "linear_equations"
    session["current_topic"] = topic_id
    session["problem_index"] = 0
    session["difficulty"] = difficulty
    return redirect(url_for("practice"))

@app.route("/practice", methods=["GET", "POST"])
def practice():
    topic_id = session.get("current_topic", "linear_equations")
    difficulty = session.get("difficulty", "easy")
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    topic = MATH_TOPICS[topic_id]
    # --- Difficulty-based filtering and randomization ---
    all_problems = topic["problems"]
    # Assign difficulty to problems by index (simple mapping for demo)
    easy_idx = int(len(all_problems) * 0.4)
    med_idx = int(len(all_problems) * 0.7)
    if difficulty == "easy":
        filtered = all_problems[:easy_idx] if easy_idx > 0 else all_problems[:1]
    elif difficulty == "medium":
        filtered = all_problems[easy_idx:med_idx] if med_idx > easy_idx else all_problems[easy_idx:]
    else:
        filtered = all_problems[med_idx:] if med_idx < len(all_problems) else all_problems[-1:]
    # If not enough, fallback to all
    if not filtered:
        filtered = all_problems
    # Shuffle for variety
    random.seed(session.get("user_id", time.time()))
    problems = filtered.copy()
    random.shuffle(problems)
    # Save the randomized order in session for consistency
    if "problem_order" not in session or session.get("difficulty_last") != difficulty or session.get("topic_last") != topic_id:
        session["problem_order"] = [all_problems.index(p) for p in problems]
        session["difficulty_last"] = difficulty
        session["topic_last"] = topic_id
        session["problem_index"] = 0
    else:
        problems = [all_problems[i] for i in session["problem_order"]]
    
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
        "practice_screen.html", 
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
    """Update user progress for a specific topic and save to Firebase if logged in"""
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
    # Save to Firebase if logged in
    if firebase_available and "user_id" in session:
        try:
            save_progress_to_firestore(session["user_id"], session["progress"])
        except Exception as e:
            print(f"Error saving progress to Firestore: {e}")

# Helper to save progress to Firestore
def save_progress_to_firestore(user_id, progress_dict):
    if not db:
        return
    doc_ref = db.collection("user_progress").document(user_id)
    doc_ref.set({"progress": progress_dict}, merge=True)

@app.route("/next", methods=["POST"])
def next_problem():
    topic_id = session.get("current_topic", "linear_equations")
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    difficulty = session.get("difficulty", "easy")
    topic = MATH_TOPICS[topic_id]
    all_problems = topic["problems"]
    easy_idx = int(len(all_problems) * 0.4)
    med_idx = int(len(all_problems) * 0.7)
    if difficulty == "easy":
        filtered = all_problems[:easy_idx] if easy_idx > 0 else all_problems[:1]
    elif difficulty == "medium":
        filtered = all_problems[easy_idx:med_idx] if med_idx > easy_idx else all_problems[easy_idx:]
    else:
        filtered = all_problems[med_idx:] if med_idx < len(all_problems) else all_problems[-1:]
    if not filtered:
        filtered = all_problems
    problems = filtered.copy()
    if "problem_order" in session:
        problems = [all_problems[i] for i in session["problem_order"]]
    idx = session.get("problem_index", 0)
    idx += 1
    # Check if all problems for this difficulty are completed
    if idx >= len(problems):
        return redirect(url_for("topic_completed", topic_id=topic_id))
    session["problem_index"] = idx
    return redirect(url_for("practice"))

@app.route("/completed/<topic_id>")
def topic_completed(topic_id):
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    topic = MATH_TOPICS[topic_id]
    user_info = None
    correct_count = 0
    incorrect_count = 0
    # Retrieve answer history from session if available
    answer_history = session.get("answer_history", {})
    topic_history = answer_history.get(topic_id, [])
    for entry in topic_history:
        if entry.get("correct"):
            correct_count += 1
        else:
            incorrect_count += 1
    if "user_id" in session:
        user_info = {
            "email": session.get("user_email"),
            "name": session.get("user_name", "User")
        }
    return render_template("topic_completed.html", user=user_info, topic=topic, topic_id=topic_id, correct_count=correct_count, incorrect_count=incorrect_count)

@app.route("/health")
def health_check():
    """Simple health check for monitoring"""
    return {"status": "healthy", "firebase": firebase_available}, 200

# ============ CHALLENGE MODE ROUTES ============

@app.route("/challenge")
def challenge_mode():
    """Challenge mode selection screen"""
    if request.method == "POST":
        user_answer = request.form.get("answer", "").strip()
        if user_answer == "":
            feedback = "Please enter an answer."
        else:
            try:
                # Handle different answer types
                if isinstance(problem["answer"], str):
                    user_answer_clean = user_answer.replace(" ", "")
                    correct_answer_clean = str(problem["answer"]).replace(" ", "")
                    if "," in correct_answer_clean and "," in user_answer_clean:
                        user_values = set(user_answer_clean.split(","))
                        correct_values = set(correct_answer_clean.split(","))
                        is_correct = user_values == correct_values
                    elif "(" in correct_answer_clean and ")" in correct_answer_clean and "(" in user_answer_clean and ")" in user_answer_clean:
                        import re
                        correct_factors = re.findall(r'\([^)]+\)', correct_answer_clean)
                        user_factors = re.findall(r'\([^)]+\)', user_answer_clean)
                        correct_factors_set = set(correct_factors)
                        user_factors_set = set(user_factors)
                        is_correct = correct_factors_set == user_factors_set
                    else:
                        is_correct = user_answer_clean.lower() == correct_answer_clean.lower()
                    if is_correct:
                        feedback = "Correct!"
                        if "user_id" in session:
                            try:
                                update_user_progress(topic_id, idx)
                            except Exception as e:
                                print(f"Progress update error: {e}")
                    else:
                        feedback = "Incorrect!"
                else:
                    try:
                        user_num = int(user_answer)
                        if user_num == problem["answer"]:
                            feedback = "Correct!"
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
        # --- Track answer history for round feedback ---
        answer_history = session.get("answer_history", {})
        topic_history = answer_history.get(topic_id, [])
        topic_history.append({"problem": idx, "correct": feedback == "Correct!", "user_answer": user_answer})
        answer_history[topic_id] = topic_history
        session["answer_history"] = answer_history
        session.modified = True

@app.route("/challenge/answer", methods=["POST"])
def submit_challenge_answer():
    """Submit answer for current challenge question"""
    if "challenge" not in session or "user_id" not in session:
        return jsonify({"error": "No active challenge"}), 400
    
    challenge = session["challenge"]
    current_round = challenge["current_round"]
    current_question = challenge["current_question"]
    
    # Get submitted answer
    user_answer = request.form.get("answer", "").strip()
    print(f"DEBUG: Received answer from user: '{user_answer}'")  # DEBUG
    time_taken = time.time() - challenge["round_start_time"]
    print(f"DEBUG: Time taken: {time_taken}")  # DEBUG
    
    # Get current question
    round_questions = challenge["questions"][current_round - 1]
    question = round_questions[current_question]
    
    # Check answer correctness
    is_correct = check_answer(user_answer, question["answer"])
    
    # Calculate score
    points = calculate_challenge_score(is_correct, time_taken, current_round)
    
    # Record answer
    answer_record = {
        "round": current_round,
        "question": current_question,
        "user_answer": user_answer,
        "correct_answer": question["answer"],
        "is_correct": is_correct,
        "time_taken": time_taken,
        "points": points,
        "topic": question.get("topic", "Math"),
        "equation": question.get("equation", ""),
        "instruction": question.get("instruction", "")
    }
    challenge["answers"].append(answer_record)
    challenge["score"] += points
    
    # Move to next question
    challenge["current_question"] += 1
    
    # Check if round is complete
    if challenge["current_question"] >= len(round_questions):
        # Round completed
        round_score = sum(ans["points"] for ans in challenge["answers"] 
                         if ans["round"] == current_round)
        challenge["round_scores"].append(round_score)
    
    session["challenge"] = challenge
    session.modified = True
    
    return jsonify({
        "correct": is_correct,
        "points": points,
        "total_score": challenge["score"],
        "correct_answer": question["answer"]
    })

@app.route("/challenge/timeout", methods=["POST"])
def challenge_timeout():
    """Handle when timer runs out"""
    print("DEBUG: Timeout route called!")  # DEBUG
    if "challenge" not in session or "user_id" not in session:
        return jsonify({"error": "No active challenge"}), 400
    
    challenge = session["challenge"]
    current_round = challenge["current_round"]
    current_question = challenge["current_question"]
    
    # Get current question
    round_questions = challenge["questions"][current_round - 1]
    question = round_questions[current_question]
    
    # Record timeout
    answer_record = {
        "round": current_round,
        "question": current_question,
        "user_answer": "",
        "correct_answer": question["answer"],
        "is_correct": False,
        "time_taken": CHALLENGE_CONFIG["time_limit_seconds"],
        "points": 0,
        "topic": question.get("topic", "Math"),
        "equation": question.get("equation", ""),
        "instruction": question.get("instruction", "")
    }
    challenge["answers"].append(answer_record)
    
    # Move to next question
    challenge["current_question"] += 1
    
    # Check if round is complete
    if challenge["current_question"] >= len(round_questions):
        round_score = sum(ans["points"] for ans in challenge["answers"] 
                         if ans["round"] == current_round)
        challenge["round_scores"].append(round_score)
    
    session["challenge"] = challenge
    session.modified = True
    
    return jsonify({"timeout": True, "correct_answer": question["answer"]})

@app.route("/challenge/complete")
def challenge_complete():
    """Show challenge completion screen and save score"""
    if "challenge" not in session or "user_id" not in session:
        return redirect(url_for("challenge_mode"))
    
    challenge = session["challenge"]
    user_info = {
        "email": session.get("user_email"),
        "name": session.get("user_name", "User"),
        "id": session.get("user_id")
    }
    
    # Calculate final statistics
    total_time = time.time() - challenge["start_time"]
    correct_answers = sum(1 for ans in challenge["answers"] if ans["is_correct"])
    total_questions = len(challenge["answers"])
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Store challenge data before clearing session
    final_score = challenge["score"]
    final_round_scores = challenge["round_scores"]
    final_answers = challenge["answers"]
    
    # Save score to leaderboard
    save_score_to_leaderboard(
        user_info["id"],
        user_info["name"],
        final_score,
        total_time,
        correct_answers,
        total_questions
    )
    
    # Clear challenge session
    del session["challenge"]
    session.modified = True
    
    return render_template("challenge_complete.html",
                         user=user_info,
                         score=final_score,
                         round_scores=final_round_scores,
                         total_time=total_time,
                         correct_answers=correct_answers,
                         total_questions=total_questions,
                         accuracy=accuracy,
                         answers=final_answers)

# ============ LEADERBOARD ROUTES ============

@app.route("/leaderboard")
def leaderboard():
    """Display leaderboard"""
    user_info = None
    if "user_id" in session:
        user_info = {
            "email": session.get("user_email"),
            "name": session.get("user_name", "User"),
            "id": session.get("user_id")
        }
    
    # Get leaderboard data
    leaderboard_data = get_leaderboard()
    user_rank = get_user_rank(session.get("user_id")) if "user_id" in session else None
    
    return render_template("leaderboard.html", 
                         user=user_info,
                         leaderboard=leaderboard_data,
                         user_rank=user_rank)

@app.route("/restart/<topic_id>", methods=["POST"])
def restart_topic(topic_id):
    if topic_id not in MATH_TOPICS:
        return redirect(url_for("topics"))
    
    session["current_topic"] = topic_id
    session["problem_index"] = 0
    return redirect(url_for("practice"))

# ============ HELPER FUNCTIONS ============

def generate_challenge_questions():
    """Generate questions for challenge mode - 3 rounds of 3 questions each"""
    all_questions = []
    
    for round_num in range(CHALLENGE_CONFIG["rounds"]):
        round_questions = []
        
        # Get all available problems from all topics
        all_problems = []
        for topic_id, topic_data in MATH_TOPICS.items():
            for i, problem in enumerate(topic_data["problems"]):
                problem_copy = problem.copy()
                problem_copy["topic"] = topic_data["title"]
                problem_copy["topic_id"] = topic_id
                all_problems.append(problem_copy)
        
        # Randomly select questions for this round
        selected_problems = random.sample(all_problems, CHALLENGE_CONFIG["questions_per_round"])
        round_questions.extend(selected_problems)
        
        all_questions.append(round_questions)
    
    return all_questions

def check_answer(user_answer, correct_answer):
    """Check if user answer matches correct answer - improved version with flexible formats"""
    if not user_answer.strip():
        return False
    
    try:
        # Clean both answers
        user_answer_clean = user_answer.replace(" ", "").lower()
        correct_answer_clean = str(correct_answer).replace(" ", "").lower()
        
        # Direct match first (handles most cases)
        if user_answer_clean == correct_answer_clean:
            return True
        
        # Handle "x=" prefix flexibility for solving equations
        # Allow both "3" and "x=3" to be correct when answer is just "3"
        if user_answer_clean.startswith('x=') and not correct_answer_clean.startswith('x='):
            # User wrote "x=3" but correct answer is just "3"
            user_value = user_answer_clean[2:]  # Remove "x="
            if user_value == correct_answer_clean:
                return True
        elif correct_answer_clean.startswith('x=') and not user_answer_clean.startswith('x='):
            # User wrote "3" but correct answer is "x=3"
            correct_value = correct_answer_clean[2:]  # Remove "x="
            if user_answer_clean == correct_value:
                return True
        
        # Handle string-based answers
        if isinstance(correct_answer, str):
            # Check if this is a comma-separated answer (like quadratic solutions)
            if "," in correct_answer_clean:
                if "," in user_answer_clean:
                    # Split and compare sets, handling x= prefix flexibility
                    user_values = set()
                    correct_values = set()
                    
                    for val in user_answer_clean.split(","):
                        val = val.strip()
                        if val.startswith('x='):
                            user_values.add(val[2:])
                        else:
                            user_values.add(val)
                    
                    for val in correct_answer_clean.split(","):
                        val = val.strip()
                        if val.startswith('x='):
                            correct_values.add(val[2:])
                        else:
                            correct_values.add(val)
                    
                    return user_values == correct_values
                else:
                    return False
            
            # Check if this is a factored expression (contains parentheses)
            elif "(" in correct_answer_clean and ")" in correct_answer_clean:
                import re
                
                # Extract factors from correct answer
                correct_factors = re.findall(r'\([^)]+\)', correct_answer_clean)
                correct_factors_set = set(correct_factors)
                
                # Try to extract factors from user answer
                if "(" in user_answer_clean and ")" in user_answer_clean:
                    user_factors = re.findall(r'\([^)]+\)', user_answer_clean)
                    user_factors_set = set(user_factors)
                    
                    # Also check for any leading coefficient
                    # Extract coefficient before parentheses
                    correct_coeff = re.findall(r'^(\d*)', correct_answer_clean)
                    user_coeff = re.findall(r'^(\d*)', user_answer_clean)
                    
                    # Check if factors match (ignoring order)
                    return (correct_factors_set == user_factors_set and 
                           correct_coeff == user_coeff)
                else:
                    return False
            
            # Regular string comparison for inequality symbols, algebraic expressions
            else:
                # Handle inequality symbols and algebraic expressions
                return user_answer_clean == correct_answer_clean
                
        else:
            # Numeric answer - try to convert both to numbers
            try:
                # Handle x= prefix for numeric answers
                user_clean = user_answer_clean
                if user_clean.startswith('x='):
                    user_clean = user_clean[2:]
                
                user_num = float(user_clean)
                correct_num = float(correct_answer)
                # Use small tolerance for floating point comparison
                return abs(user_num - correct_num) < 0.0001
            except ValueError:
                return False
                
    except Exception as e:
        print(f"Answer checking error: {e}")
        return False

def calculate_challenge_score(is_correct, time_taken, round_number):
    """Calculate score for a challenge question"""
    if not is_correct:
        return 0
    
    base_points = CHALLENGE_CONFIG["points"]["correct_answer"]
    
    # Speed bonus (more points for faster answers)
    time_limit = CHALLENGE_CONFIG["time_limit_seconds"]
    speed_ratio = max(0, (time_limit - time_taken) / time_limit)
    speed_bonus = int(speed_ratio * CHALLENGE_CONFIG["points"]["speed_bonus_max"])
    
    # Round multiplier
    round_multiplier = CHALLENGE_CONFIG["points"]["round_multipliers"][round_number - 1]
    
    total_points = int((base_points + speed_bonus) * round_multiplier)
    return total_points

def save_score_to_leaderboard(user_id, username, score, total_time, correct_answers, total_questions):
    """Save user score to Firebase leaderboard"""
    if not firebase_available or not db:
        # Fallback: save to session for local testing
        if "local_leaderboard" not in session:
            session["local_leaderboard"] = []
        
        session["local_leaderboard"].append({
            "user_id": user_id,
            "username": username,
            "score": score,
            "total_time": total_time,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "accuracy": (correct_answers / total_questions * 100) if total_questions > 0 else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        session.modified = True
        return
    
    try:
        # Save to Firebase
        doc_data = {
            "user_id": user_id,
            "username": username,
            "score": score,
            "total_time": total_time,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "accuracy": (correct_answers / total_questions * 100) if total_questions > 0 else 0,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Add to leaderboard collection
        db.collection("leaderboard").add(doc_data)
        
        # Also update user's best score if this is better
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            best_score = user_data.get("best_score", 0)
            if score > best_score:
                user_ref.update({"best_score": score, "best_score_date": datetime.now(timezone.utc)})
        else:
            user_ref.set({
                "username": username, 
                "best_score": score, 
                "best_score_date": datetime.now(timezone.utc)
            })
            
    except Exception as e:
        print(f"Error saving to leaderboard: {e}")

def get_leaderboard(limit=10):
    """Get top scores from leaderboard"""
    if not firebase_available or not db:
        # Fallback: get from session
        local_scores = session.get("local_leaderboard", [])
        return sorted(local_scores, key=lambda x: x["score"], reverse=True)[:limit]
    
    try:
        # Get from Firebase
        query = db.collection("leaderboard").order_by("score", direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        
        leaderboard = []
        for doc in docs:
            data = doc.to_dict()
            leaderboard.append(data)
        
        return leaderboard
        
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []

def get_user_rank(user_id):
    """Get user's rank in leaderboard"""
    if not user_id:
        return None
        
    if not firebase_available or not db:
        # Fallback: calculate from session
        local_scores = session.get("local_leaderboard", [])
        sorted_scores = sorted(local_scores, key=lambda x: x["score"], reverse=True)
        
        for i, entry in enumerate(sorted_scores):
            if entry["user_id"] == user_id:
                return {
                    "rank": i + 1,
                    "score": entry["score"],
                    "accuracy": entry["accuracy"]
                }
        return None
    
    try:
        # Get user's best score
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return None
            
        user_best = user_doc.to_dict().get("best_score", 0)
        
        # Count how many users have better scores
        better_scores = db.collection("users").where("best_score", ">", user_best).get()
        rank = len(better_scores) + 1
        
        return {
            "rank": rank,
            "score": user_best
        }
        
    except Exception as e:
        print(f"Error getting user rank: {e}")
        return None

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Use debug=False in production for better performance
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)