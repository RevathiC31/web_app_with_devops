
from app import db, User

def test_health_endpoint(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json.get('status') == 'ok'

def test_user_register_and_login_flow(client):
    # Register
    resp = client.post('/register', data={
        'username': 'alice',
        'password': 'secret123'
    }, follow_redirects=True)
    assert resp.status_code == 200

    # Login
    resp = client.post('/login', data={
        'username': 'alice',
        'password': 'secret123'
    }, follow_redirects=True)
    assert resp.status_code == 200

def test_upload_and_list_files(client):
    # Create a user and login
    with client.application.app_context():
        user = User(username='bob', password='hash')
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['user_id'] = user_id

    # Upload
    data = {
        'file': (bytes("hello", "utf-8"), 'hello.txt')
    }
    resp = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert resp.status_code == 200

    # Dashboard shows file
    resp = client.get('/dashboard')
    assert resp.status_code == 200
    assert b'hello.txt' in resp.data
