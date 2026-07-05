from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

document_id = '6c0abe44-0fa8-46f9-858f-47f947e53c81'
response = client.get(f'/api/documents/{document_id}/notes')
print('status', response.status_code)
print(response.text)
