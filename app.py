from flask import Flask, render_template, request

app = Flask(__name__)

PROBLEM = {
    "question" : "What is 2 + 2?", 
    "answer" : 4
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
    return render_template("index.html", question=PROBLEM["question"], feedback=feedback, user_answer=user_answer)
if __name__ == '__main__':
    app.run(debug=True, port=5002)