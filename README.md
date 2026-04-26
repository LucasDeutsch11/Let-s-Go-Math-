# Let's Go Math!

**Let's Go Math!** is an interactive algebra practice web app built with Flask and Firebase. Students can practice algebra topics at their own pace, track their progress, and compete in timed challenge rounds.

---

## Features

- **8 Algebra Topics** — Linear Equations, Inequalities, Systems of Equations, Exponents, Polynomials, Factoring, Quadratic Equations, and Word Problems
- **3 Difficulty Levels** — Easy, Medium, and Hard for each topic (5 problems each)
- **Instant Feedback** — Correct/incorrect feedback on every answer
- **Progress Tracking** — Track completed problems per topic saved to Firebase Firestore
- **Challenge Mode** — Timed multi-round competition with mixed algebra problems and speed bonuses
- **Leaderboard** — Top scores displayed from Firebase on the leaderboard page
- **User Accounts** — Sign up, sign in, and reset password via Firebase Authentication

---

## Tech Stack

- **Backend:** Python 3, Flask
- **Database / Auth:** Firebase (Firestore + Firebase Authentication)
- **Frontend:** HTML, CSS, JavaScript (no frameworks)
- **Deployment:** Render (using Gunicorn)

---

## How to Run Locally

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd LetsGoMath
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add Firebase credentials**
   - Place your `serviceAccountKey.json` file in the project root.
   - This file is required for Firebase Admin SDK (Firestore + Auth).

5. **Run the app**
   ```bash
   flask run
   ```
   or
   ```bash
   python app.py
   ```
   Then open `http://localhost:5000` in your browser.

---

## Deployment (Render)

The app is deployed on [Render](https://render.com) using Gunicorn:

- **Start command:** `gunicorn app:app`
- Set the `SECRET_KEY` environment variable in the Render dashboard.
- Upload `serviceAccountKey.json` as a secret file (or use environment variables for credentials).

---

## Project Iterations

| Cycle | Description |
|-------|-------------|
| 1 | Hello World — local Flask app with one practice problem and feedback |
| 2 | Multiple algebra topics, difficulty selection, answer checking |
| 3 | User accounts with Firebase Authentication and progress tracking |
| 4 | Firebase Firestore for persistent progress storage, improved UI |
| 5 | Challenge Mode with timed rounds, scoring, and leaderboard |
| 6 | Final polish — consistent UI/UX, navigation improvements, bug fixes, README update |

---

## Pages

| Route | Description |
|-------|-------------|
| `/` | Home screen |
| `/topics` | Browse all algebra topics |
| `/topic/<id>` | Topic detail with difficulty selection |
| `/practice` | Active practice problem |
| `/dashboard` | User progress dashboard |
| `/login` | Sign in |
| `/signup` | Create account |
| `/challenge` | Challenge mode info page |
| `/challenge/round` | Active challenge question |
| `/challenge/complete` | Challenge results |
| `/leaderboard` | Top scores |

---

© 2026 Let's Go Math

