import os
import csv
from flask import Flask, request, jsonify, send_file
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd

app = Flask(__name__)

# === Configuration ===
PDF_FOLDER = "pdfs"
LOG_FOLDER = "logs"
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# === Data Definitions ===
theory_subjects = [
    "biology", "mathematics", "communication_skill", "electrical_engineering",
    "mechanical_engineering", "environmental_science", "physics"
]

lab_subjects = [
    "physics_lab1", "physics_lab2", "engineering_graphics_lab", "workshop",
    "mechanics_lab", "chemistry_lab", "language_lab", "design_thinking_lab"
]

exam_types = ["mid_sem1", "mid_sem2", "end_sem"]
unit_types = [f"unit{i}" for i in range(1, 6)]
years = ["2024", "2023"]

# === Routes ===

@app.route("/")
def home():
    return "\u2705 Backend is running!"

@app.route("/subjects")
def get_subjects():
    return jsonify({"theory": theory_subjects, "labs": lab_subjects})

@app.route("/options/<subject>")
def get_options(subject):
    if subject in theory_subjects:
        return jsonify(exam_types + unit_types)
    elif subject in lab_subjects:
        return jsonify(["material"])
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

    filename = build_filename(subject, exam_type, year)
    file_path = os.path.join(PDF_FOLDER, filename)

    if os.path.isfile(file_path):
        log_download(user_id, subject, exam_type, year)
        return send_file(file_path, mimetype="application/pdf",
                         download_name=filename,
                         as_attachment=False)
    return "PDF Not Found", 404

@app.route("/download-url/<path:filename>")
def serve_pdf_inline(filename):
    file_path = os.path.join(PDF_FOLDER, filename)
    if os.path.isfile(file_path):
        return send_file(file_path, mimetype="application/pdf",
                         download_name=filename,
                         as_attachment=False)
    return "File not found", 404

# === Helper Functions ===

def build_filename(subject, exam_type, year):
    if exam_type == "material":
        return f"{subject}_material.pdf"
    elif exam_type.startswith("unit"):
        return f"{subject}_{exam_type}.pdf"
    else:
        return f"{subject}_{exam_type}_{year}.pdf"

def log_download(user_id, subject, exam_type, year):
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(log_file)

    with open(log_file, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "User", "Subject", "ExamType", "Year"])
        writer.writerow([timestamp, user_id, subject, exam_type, year])

# === Scheduled Jobs ===

def clean_logs():
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")
    if not os.path.isfile(log_file):
        return

    try:
        df = pd.read_csv(log_file, parse_dates=["Timestamp"])
        cutoff = datetime.now() - timedelta(days=30)
        df = df[df["Timestamp"] >= cutoff]
        df.to_csv(log_file, index=False)
    except Exception as e:
        print("Log cleanup error:", e)

def send_weekly_report():
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")
    if not os.path.isfile(log_file):
        return

    try:
        df = pd.read_csv(log_file)
        total = len(df)
        top_subjects = df["Subject"].value_counts().head(3)
        top_users = df["User"].value_counts().head(3)

        print("\n\U0001F4CA Weekly Report")
        print("Total Downloads:", total)
        print("Top Subjects:")
        print(top_subjects)
        print("Top Users:")
        print(top_users)
    except Exception as e:
        print("Report error:", e)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(clean_logs, 'cron', hour=3)
    scheduler.add_job(send_weekly_report, 'cron', day_of_week='mon', hour=9)
    scheduler.start()

# === Run App ===
if __name__ == "__main__":
    start_scheduler()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
