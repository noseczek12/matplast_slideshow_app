from flask import Flask, request, send_from_directory, jsonify, render_template, redirect
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return redirect('/kiosk')

@app.route('/kiosk')
def kiosk():
    return render_template('kiosk.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/images')
def get_images():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    images = [f'/static/uploads/{f}' for f in files if allowed_file(f)]
    return jsonify(images)

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return 'File uploaded', 200
    return 'Invalid file type', 400

@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return 'Deleted', 200
    return 'File not found', 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')