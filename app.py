from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

DB_PATH = os.path.join(os.path.dirname(__file__), "hostelfix.db")

CATEGORIES = ["Electrical", "Plumbing", "Furniture", "Cleanliness", "Internet/WiFi", "Other"]

HIGH_PRIORITY_KEYWORDS = [
    "fire", "gas", "smoke", "spark", "shock", "flood", "flooding",
    "electric shock", "short circuit", "burning", "no water", "leak"
]
MEDIUM_PRIORITY_KEYWORDS = [
    "broken", "not working", "damaged", "stuck", "leaking", "blocked",
    "clogged", "no power", "slow", "noisy"
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room_no TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def analyze_priority(description: str) -> str:
    """Very simple keyword-based priority detection.
    Swap this out for a real model/API call if you want smarter analysis."""
    text = description.lower()
    if any(word in text for word in HIGH_PRIORITY_KEYWORDS):
        return "High"
    if any(word in text for word in MEDIUM_PRIORITY_KEYWORDS):
        return "Medium"
    return "Low"


@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    room_no = request.form.get("room_no", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()

    if not all([name, room_no, category, description]):
        flash("Please fill in every field before submitting.", "error")
        return redirect(url_for("index"))

    priority = analyze_priority(description)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    conn.execute(
        """INSERT INTO complaints (name, room_no, category, description, priority, status, created_at)
           VALUES (?, ?, ?, ?, ?, 'Pending', ?)""",
        (name, room_no, category, description, priority, created_at),
    )
    conn.commit()
    conn.close()

    flash(f"Complaint submitted — flagged as {priority} priority.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    conn = get_db()
    complaints = conn.execute(
        "SELECT * FROM complaints ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    stats = {
        "pending": sum(1 for c in complaints if c["status"] == "Pending"),
        "in_progress": sum(1 for c in complaints if c["status"] == "In Progress"),
        "resolved": sum(1 for c in complaints if c["status"] == "Resolved"),
        "high_priority": sum(1 for c in complaints if c["priority"] == "High"),
    }

    return render_template("dashboard.html", complaints=complaints, stats=stats)


@app.route("/admin")
def admin():
    conn = get_db()
    complaints = conn.execute(
        "SELECT * FROM complaints ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("admin.html", complaints=complaints)


@app.route("/admin/update/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):
    new_status = request.form.get("status")
    if new_status not in ("Pending", "In Progress", "Resolved"):
        flash("Invalid status.", "error")
        return redirect(url_for("admin"))

    conn = get_db()
    conn.execute(
        "UPDATE complaints SET status = ? WHERE id = ?", (new_status, complaint_id)
    )
    conn.commit()
    conn.close()

    flash("Status updated.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/delete/<int:complaint_id>", methods=["POST"])
def delete_complaint(complaint_id):
    conn = get_db()
    conn.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
    conn.commit()
    conn.close()
    flash("Complaint removed.", "success")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)