from flask import Flask, render_template, request
import os

app = Flask(__name__)

PROBLEM = {
    "instruction" : "Solve for",
    "variable" : "x",
    "equation" : "x + 5 = 7",
    "answer" : 2
}

@app.route("/", methods=["GET", "POST"])
def home():
    feedback = None
    user_answer = ""
    
    if request.method == "POST" :
        user_answer = request.form.get("answer", "").strip()

        if user_answer == "":
            feedback = "Please enter an answer."
        else:
            try:
                user_num = int(user_answer)
                if user_num == PROBLEM["answer"] :
                    feedback = "Correct!"
                else:
                    feedback = "Incorrect!"
            except ValueError:
                feedback = "Please enter a valid whole number."
    return render_template(
        "index.html", 
        instruction=PROBLEM["instruction"], 
        variable=PROBLEM["variable"],
        equation=PROBLEM["equation"],
        feedback=feedback, 
        user_answer=user_answer
    )
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)