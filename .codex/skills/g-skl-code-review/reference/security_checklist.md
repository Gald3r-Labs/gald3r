# Security Review Checklist

Comprehensive security vulnerabilities to check during code review.

---

## OWASP Top 10 (2021)

### 1. Broken Access Control

**What to Check:**
- [ ] Authentication required for protected endpoints
- [ ] Authorization checks verify user permissions
- [ ] Users can't access others' data
- [ ] Admin-only functions require admin check
- [ ] File access properly restricted

**Examples:**
```python
# ❌ BAD
@app.route('/api/orders/<order_id>')
def get_order(order_id):
    return Order.query.get(order_id)

# ✅ GOOD
@app.route('/api/orders/<order_id>')
@login_required
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return order
```

---

### 2. Cryptographic Failures

**What to Check:**
- [ ] Passwords are hashed (bcrypt, argon2, PBKDF2)
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS used for all sensitive transmissions
- [ ] Strong encryption algorithms (AES-256, not DES)
- [ ] Proper key management
- [ ] No hardcoded secrets

**Examples:**
```python
# ❌ BAD
user.password = request.form['password']  # Plain text!
api_key = "sk-1234567890"  # Hardcoded!

# ✅ GOOD
from werkzeug.security import generate_password_hash
user.password = generate_password_hash(request.form['password'])
api_key = os.getenv('API_KEY')
```

---

### 3. Injection

**What to Check:**
- [ ] SQL queries use parameterized statements
- [ ] User input not directly in queries
- [ ] Command injection prevented
- [ ] LDAP injection prevented
- [ ] NoSQL injection prevented

**SQL Injection:**
```python
# ❌ VULNERABLE
query = f"SELECT * FROM users WHERE id={user_id}"
query = "DELETE FROM posts WHERE id=" + request.GET['id']

# ✅ SAFE
query = "SELECT * FROM users WHERE id=%s"
cursor.execute(query, (user_id,))
```

**Command Injection:**
```python
# ❌ VULNERABLE
os.system(f"ping {user_input}")
subprocess.run(f"git clone {repo_url}", shell=True)

# ✅ SAFE
subprocess.run(['ping', user_input], shell=False)
subprocess.run(['git', 'clone', repo_url], shell=False)
```

---

### 4. Insecure Design

**What to Check:**
- [ ] Security requirements defined
- [ ] Threat modeling performed
- [ ] Defense in depth implemented
- [ ] Fail securely (deny by default)
- [ ] Separation of duties

---

### 5. Security Misconfiguration

**What to Check:**
- [ ] Debug mode disabled in production
- [ ] Default credentials changed
- [ ] Unnecessary features disabled
- [ ] Error messages don't leak info
- [ ] Security headers configured

**Examples:**
```python
# ❌ BAD
app.config['DEBUG'] = True  # In production!
app.config['SECRET_KEY'] = 'default'

# ✅ GOOD
app.config['DEBUG'] = os.getenv('DEBUG', 'False') == 'True'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
```

---

### 6. Vulnerable and Outdated Components

**What to Check:**
- [ ] Dependencies up to date
- [ ] No known vulnerabilities (npm audit, safety)
- [ ] Unused dependencies removed
- [ ] Security patches applied

**Commands:**
```bash
# Python
pip install safety
safety check

# Node.js
npm audit
npm audit fix

# Ruby
bundle audit
```

---

### 7. Identification and Authentication Failures

**What to Check:**
- [ ] Strong password policy enforced
- [ ] Multi-factor authentication available
- [ ] Session management secure
- [ ] Credential stuffing prevented
- [ ] Brute force protection (rate limiting)

**Examples:**
```python
# Session Security
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# Rate Limiting
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def login():
    ...
```

---

### 8. Software and Data Integrity Failures

**What to Check:**
- [ ] Unsigned/unverified updates prevented
- [ ] CI/CD pipeline secured
- [ ] Dependencies from trusted sources
- [ ] Integrity checks on critical data
- [ ] Deserialization of untrusted data avoided

**Examples:**
```python
# ❌ VULNERABLE
import pickle
data = pickle.loads(user_input)  # Can execute arbitrary code!

# ✅ SAFE
import json
data = json.loads(user_input)  # Safe deserialization
```

---

### 9. Security Logging and Monitoring Failures

**What to Check:**
- [ ] Security events logged
- [ ] Login attempts logged
- [ ] Failed access attempts logged
- [ ] Logs protected from tampering
- [ ] Alerts for suspicious activity

**Examples:**
```python
import logging

# Log security events
logging.warning(f"Failed login attempt for {email} from {request.remote_addr}")
logging.error(f"Unauthorized access attempt to {endpoint} by user {user_id}")

# Don't log sensitive data
logging.info(f"User {user_id} logged in")  # ✅ OK
logging.info(f"Password: {password}")  # ❌ Never log passwords!
```

---

### 10. Server-Side Request Forgery (SSRF)

**What to Check:**
- [ ] User-provided URLs validated
- [ ] Internal IPs blocked
- [ ] URL whitelist enforced
- [ ] Response from user URLs sanitized

**Examples:**
```python
# ❌ VULNERABLE
import requests
url = request.form['url']
response = requests.get(url)  # Can access internal services!

# ✅ SAFE
import requests
from urllib.parse import urlparse

def is_safe_url(url):
    parsed = urlparse(url)
    # Block internal IPs
    if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
        return False
    if parsed.hostname.startswith('192.168.'):
        return False
    if parsed.hostname.startswith('10.'):
        return False
    return True

url = request.form['url']
if not is_safe_url(url):
    abort(400, "Invalid URL")
response = requests.get(url, timeout=5)
```

---

## Additional Security Checks

### Cross-Site Scripting (XSS)

**What to Check:**
- [ ] User input properly escaped
- [ ] HTML sanitization on rich text
- [ ] Content-Security-Policy header set
- [ ] Avoid innerHTML with user data

**Examples:**
```javascript
// ❌ VULNERABLE
div.innerHTML = user_input;
document.write(user_data);

// ✅ SAFE
div.textContent = user_input;  // Auto-escapes
// Or use framework escaping (React, Vue)
```

### Cross-Site Request Forgery (CSRF)

**What to Check:**
- [ ] CSRF tokens on state-changing operations
- [ ] SameSite cookie attribute set
- [ ] Verify Origin/Referer headers

**Examples:**
```python
# Flask-WTF automatically adds CSRF protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# In templates
<form method="POST">
    {{ form.csrf_token }}
    ...
</form>
```

### File Upload Security

**What to Check:**
- [ ] File type validation
- [ ] File size limits
- [ ] Filename sanitization
- [ ] Files stored outside webroot
- [ ] Virus scanning on uploads

**Examples:**
```python
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file or file.filename == '':
        abort(400, "No file provided")

    if not allowed_file(file.filename):
        abort(400, "File type not allowed")

    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        abort(400, "File too large")

    # Sanitize filename
    filename = secure_filename(file.filename)

    # Save outside webroot
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
```

---

## Secret Detection

**What to Check:**
- [ ] No hardcoded passwords
- [ ] No API keys in code
- [ ] No AWS credentials
- [ ] No database credentials
- [ ] .env files in .gitignore

**Common Patterns to Search:**
```regex
password\s*=\s*["'][^"']+["']
api_key\s*=\s*["'][^"']+["']
secret\s*=\s*["'][^"']+["']
token\s*=\s*["'][^"']+["']
AWS_ACCESS_KEY_ID
PRIVATE_KEY
```

**Tool:**
```bash
# Use gitleaks or trufflehog
gitleaks detect --source . --verbose
```

---

## Security Headers

**What to Set:**
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

---

## Quick Security Scan Commands

**Python:**
```bash
# Check for known vulnerabilities
pip install safety
safety check

# Static analysis
pip install bandit
bandit -r .

# Dependency check
pip list --outdated
```

**Node.js:**
```bash
# Check for vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix

# Check dependencies
npm outdated
```

**General:**
```bash
# Search for secrets
git grep -i "password\|api_key\|secret"

# Check .env files
cat .env  # Should be in .gitignore!

# Find large files (potential data leaks)
find . -type f -size +10M
```

---

**Use this checklist for every code review to ensure comprehensive security coverage.**
