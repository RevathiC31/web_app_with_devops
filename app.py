
"""
Flask File Manager

A Flask-based web application for user registration, authentication,
and secure file management (upload, view, download, delete).
"""

import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, session, \
    send_from_directory, flash, send_file, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
app = Flask(__name__)

# Prefer environment variables for secrets/configs
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///site.db')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
# Default 16GB
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', str(16 * 1024 * 1024 * 1024)))

db = SQLAlchemy(app)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class User(db.Model):  # pylint: disable=too-few-public-methods
    """Database model for users."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    files = db.relationship('File', backref='owner', lazy=True)


class File(db.Model):  # pylint: disable=too-few-public-methods
    """Database model for uploaded files."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


def get_file_by_id(file_id: int):
    """Retrieve a file record by its ID."""
    return File.query.get(file_id)

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route('/health')
def health():
    """Health check endpoint for monitoring and readiness probes."""
    return {"status": "ok"}, 200


@app.route('/')
def home():
    """Render login or redirect to dashboard if logged in."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password_raw = request.form['password']
        if not username or not password_raw:
            flash("Username and password are required.")
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.")
            return redirect(url_for('register'))

        password = generate_password_hash(password_raw)
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password_input = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password_input):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash("Invalid username or password.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Log the user out and clear the session."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    """Display the user's dashboard with uploaded files."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    user_files = File.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', files=user_files, username=user.username)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    if 'user_id' not in session:
        flash("You must be logged in to upload files.")
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_file = File(filename=filename, path=filepath, user_id=session['user_id'])
        db.session.add(new_file)
        db.session.commit()

        flash('File uploaded successfully')
        return redirect(url_for('dashboard'))

    flash('No file provided')
    return redirect(url_for('dashboard'))


@app.route('/download/<int:file_id>')
def download_file(file_id):
    """Allow the user to download a file by ID."""
    file = File.query.get_or_404(file_id)
    if file.user_id != session.get('user_id'):
        flash("Unauthorized access.")
        return redirect(url_for('dashboard'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename, as_attachment=True)


@app.route('/view/<int:file_id>')
def view_file(file_id):
    """Allow the user to view a file in the browser."""
    file = get_file_by_id(file_id)
    if not file:
        abort(404, description="File not found")
    if file.user_id != session.get('user_id'):
        flash("Unauthorized access.")
        return redirect(url_for('dashboard'))
    if not os.path.exists(file.path):
        abort(404, description="File does not exist on server")
    mime_type, _ = mimetypes.guess_type(file.path)
    if not mime_type:
        mime_type = 'application/octet-stream'
    return send_file(file.path, mimetype=mime_type)


@app.route('/delete/<int:file_id>')
def delete_file(file_id):
    """Delete a file uploaded by the user."""
    file = File.query.get_or_404(file_id)
    if file.user_id != session.get('user_id'):
        flash("Unauthorized action.")
        return redirect(url_for('dashboard'))
    try:
        os.remove(file.path)
    except FileNotFoundError:
        pass
    db.session.delete(file)
    db.session.commit()
    flash("File deleted.")
    return redirect(url_for('dashboard'))


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')
