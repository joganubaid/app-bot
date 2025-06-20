from flask import Flask, jsonify, request, send_file
import os

app = Flask(__name__)
PDF_FOLDER = "pdfs"

# ✅ Root route for UptimeRobot or Render health check
@app.route("/")
def home():
    return "✅ Bot is running!"

# All subjects categorized
subjects = {
    "theory": [
        "biology", "mathematics", "communication_skill", "electrical_engineering",
        "mechanical_engineering", "environmental_science", "physics"
    ],
    "labs": [
        "physics_lab1", "physics_lab2", "engineering_graphics_lab", "workshop",
        "mechanics_lab", "chemistry_lab", "language_lab", "design_thinking_lab"
    ]
}

@app.route("/subjects")
def get_subjects():
    return jsonify(subjects)

@app.route("/options/<subject>")
def get_options(subject):
    if subject in subjects["labs"]:
        return jsonify(["material"])
    return jsonify(["mid_sem1", "mid_sem2", "end_sem", "unit1", "unit2", "unit3", "unit4", "unit5"])

@app.route("/years/<subject>/<exam_type>")
def get_years(subject, exam_type):
    return jsonify(["2024", "2023"])

@app.route("/download", methods=["POST"])
def download():
    data = request.json
    subject = data.get("subject")
    exam = data.get("exam_type")
    year = data.get("year")

    if exam.startswith("unit") or exam == "material":
        filename = f"{subject}_{exam}.pdf"
    else:
        filename = f"{subject}_{exam}_{year}.pdf"

    file_path = os.path.join(PDF_FOLDER, filename)
    if not os.path.isfile(file_path):
        return jsonify({"error": f"❌ PDF '{filename}' not found."}), 404

    return send_file(file_path, as_attachment=True)

# ✅ Required for Render: bind to 0.0.0.0 and use $PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
