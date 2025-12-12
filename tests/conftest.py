
import os
import pytest
from app import app, db, User

@pytest.fixture
def client(tmp_path):
    # Use a temporary sqlite DB for tests
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_path}/test.db"
    app.config['UPLOAD_FOLDER'] = str(tmp_path / "uploads")
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as client:
        yield client

    # Cleanup not strictly required due to tmp_path
