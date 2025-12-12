# web_app_with_devops

A Flask-based web application for user registration, authentication, and secure file management.

## Features
- User registration/login (hashed passwords)
- File: upload, view (MIME-based), download, delete
- User-specific file access control
- SQLite + SQLAlchemy
- Flash messages for feedback
- Health endpoint (`/health`) for readiness probes

## Quickstart (Local)
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
