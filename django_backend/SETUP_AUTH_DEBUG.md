# Auth Diagnostics

- Canonical endpoints:
  - POST /api/auth/token/ (SimpleJWT obtain pair; body: username+password or identifier+password)
  - POST /api/auth/register/ (body: email, username, password)

- Debug endpoint:
  - GET /api/auth/debug/ -> returns resolved path, method, and trailing slash notes

- Logging
  - Auth views log payload keys only (not values), and structured error responses.

- Tests
  - api/tests_auth_debug.py contains smoke tests for debug, register, and login.
