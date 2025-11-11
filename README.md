# corporate-learning-management-platform-222213-222228

New endpoint: POST /api/auth/register/
- Body JSON: { "username": "user1", "email": "u1@example.com", "password": "StrongPass!234", "first_name": "U", "last_name": "One", "auto_login": true }
- Response: 201 with { "user": { ... }, "tokens": { "refresh": "...", "access": "..." } } when auto_login is true.

Quick verify (from container shell or local):
curl -s -X POST http://localhost:3001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"t@e.com","password":"Str0ng!Pass","auto_login":true}'