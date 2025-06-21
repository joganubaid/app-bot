import os
import csv
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timedelta
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd

app = Flask(__name__)

# Configuration
PDF_FOLDER = "pdfs"
LOG_FOLDER = "logs"
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Subject structure
theory_subjects = [
    "biology", "mathematics", "communication_skill", "electrical_engineering",
    "mechanical_engineering", "environmental_science", "physics"
]

lab_subjects = [
    "physics_lab1", "physics_lab2", "engineering_graphics_lab", "workshop",
    "mechanics_lab", "chemistry_lab", "language_lab", "design_thinking_lab"
]

# Exam types
exam_types = ["mid_sem1", "mid_sem2", "end_sem"]
unit_types = [f"unit{i}" for i in range(1, 6)]
years = ["2024", "2023"]

# Routes
@app.route("/")
def home():
    return "✅ Backend is running!"

@app.route("/subjects")
def get_subjects():
    return jsonify({"theory": theory_subjects, "labs": lab_subjects})

@app.route("/options/<subject>")
def get_options(subject):
    if subject in theory_subjects:
        return jsonify(exam_types + unit_types)
    elif subject in lab_subjects:
        return jsonify(["material"])
    else:
        return jsonify([])

@app.route("/years/<subject>/<exam_type>")
def get_years(subject, exam_type):
    if subject in theory_subjects and exam_type in exam_types:
        return jsonify(years)
    return jsonify([])

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    subject = data.get("subject")
    exam_type = data.get("exam_type")
    year = data.get("year", "")
    user_id = data.get("user_id", "unknown")

    if not subject or not exam_type:
        return "Missing fields", 400

    if exam_type == "material":
        filename = f"{subject}_material.pdf"
    elif exam_type.startswith("unit"):
        filename = f"{subject}_{exam_type}.pdf"
    else:
        filename = f"{subject}_{exam_type}_{year}.pdf"

    file_path = os.path.join(PDF_FOLDER, filename)

    if os.path.isfile(file_path):
        log_download(user_id, subject, exam_type, year)
        return send_from_directory(PDF_FOLDER, filename)
    else:
        return "PDF Not Found", 404

@app.route("/download-url/<filename>")
def download_url(filename):
    if os.path.isfile(os.path.join(PDF_FOLDER, filename)):
        return send_from_directory(PDF_FOLDER, filename)
    return "File not found", 404

# Logging
def log_download(user_id, subject, exam_type, year):
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = str(user_id)

    file_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "User", "Subject", "ExamType", "Year"])
        writer.writerow([timestamp, username, subject, exam_type, year])

# Auto-clean logs older than 30 days
def clean_logs():
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")
    if not os.path.isfile(log_file):
        return

    df = pd.read_csv(log_file, parse_dates=["Timestamp"])
    df = df[df["Timestamp"] >= (datetime.now() - timedelta(days=30))]
    df.to_csv(log_file, index=False)

# Weekly report (optional log to console or admin)
def send_weekly_report():
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")
    if not os.path.isfile(log_file):
        return

    try:
        df = pd.read_csv(log_file)
        total = len(df)
        subject_counts = df["Subject"].value_counts().head(3)
        user_counts = df["User"].value_counts().head(3)

        print("📊 Weekly Report")
        print("Total Downloads:", total)
        print("Top Subjects:")
        print(subject_counts)
        print("Top Users:")
        print(user_counts)
    except Exception as e:
        print("Report error:", e)

# Schedule report
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_weekly_report, 'cron', day_of_week='mon', hour=9, minute=0)
    scheduler.add_job(clean_logs, 'cron', hour=3)
    scheduler.start()

# Run
if __name__ == "__main__":
    start_scheduler()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
