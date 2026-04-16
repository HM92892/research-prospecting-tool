import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_uploaded_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            files.append({"name": filename, "size": size})
    files.sort(key=lambda x: x["name"])
    return files


@app.route("/")
def index():
    files = get_uploaded_files()
    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        flash("No files selected.", "error")
        return redirect(url_for("index"))

    uploaded_files = request.files.getlist("files")
    success_count = 0

    for file in uploaded_files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            if filename:
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                success_count += 1

    if success_count > 0:
        flash(f"{success_count} file(s) uploaded successfully.", "success")
    else:
        flash("No valid files were uploaded.", "error")

    return redirect(url_for("index"))


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
    if os.path.isfile(filepath):
        os.remove(filepath)
        flash(f'"{filename}" deleted.', "success")
    else:
        flash("File not found.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
