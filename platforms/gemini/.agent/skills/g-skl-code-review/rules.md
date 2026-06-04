# gald3r Code Reviewer - Implementation Rules

This document contains detailed implementation rules for performing comprehensive code reviews.

---

## Review Process Workflow

### Step 1: Initial Assessment

**Determine Review Scope:**
1. Count lines of code changed
2. Identify file types (frontend, backend, config, tests)
3. Assess criticality (auth, payment, data handling)
4. Select review type (Quick/Standard/Comprehensive)

**Review Type Selection:**
- **Quick**: < 100 lines, non-critical
- **Standard**: 100-500 lines, typical features
- **Comprehensive**: > 500 lines OR critical code

---

### Step 2: Security Scan (CRITICAL - Always First)

**Check for Common Vulnerabilities:**

#### 1. SQL Injection
```python
# ❌ VULNERABLE
query = f"SELECT * FROM users WHERE username='{user_input}'"
query = "SELECT * FROM users WHERE id=" + request.GET['id']

# ✅ SAFE
query = "SELECT * FROM users WHERE username=%s"
cursor.execute(query, (user_input,))
```

#### 2. XSS (Cross-Site Scripting)
```javascript
// ❌ VULNERABLE
div.innerHTML = user_input;
document.write(user_data);

// ✅ SAFE
div.textContent = user_input;
// Or use framework escaping: React, Vue auto-escape
```

#### 3. Authentication/Authorization
```python
# ❌ MISSING AUTH CHECK
@app.route('/admin/users')
def admin_users():
    return render_template('users.html')

# ✅ PROPER AUTH
@app.route('/admin/users')
@require_admin  # or equivalent decorator
def admin_users():
    if not current_user.is_admin:
        abort(403)
    return render_template('users.html')
```

#### 4. Sensitive Data Exposure
```python
# ❌ EXPOSED SECRETS
API_KEY = "sk-1234567890abcdef"  # Hardcoded
password = "admin123"  # In code

# ✅ PROPER HANDLING
API_KEY = os.getenv('API_KEY')  # From environment
password = os.getenv('DB_PASSWORD')
# And ensure .env is in .gitignore
```

#### 5. Input Validation
```python
# ❌ NO VALIDATION
age = request.form['age']
email = request.form['email']
file = request.files['upload']

# ✅ PROPER VALIDATION
age = int(request.form.get('age', 0))
if not 0 < age < 150:
    raise ValueError("Invalid age")

if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
    raise ValueError("Invalid email")

if file and allowed_file(file.filename):
    # Process file
```

**Security Severity Levels:**
- **CRITICAL**: Immediate fix required (SQL injection, auth bypass)
- **HIGH**: Fix before merge (XSS, secret exposure)
- **MEDIUM**: Fix soon (weak validation, insecure config)
- **LOW**: Consider fixing (missing rate limiting, verbose errors)

---

### Step 3: Code Quality Assessment

#### File Size Check
```
< 200 lines: ✅ Good
200-500 lines: ⚠️ Consider refactoring
500-800 lines: ⚠️ Should refactor
> 800 lines: ❌ Must refactor
```

**Refactoring Guidance:**
- Break into logical modules
- Extract reusable functions
- Separate concerns (UI, business logic, data access)
- Use classes/modules for organization

#### Function Complexity
```
< 20 lines: ✅ Good
20-50 lines: ⚠️ Acceptable
50-100 lines: ⚠️ Consider breaking up
> 100 lines: ❌ Too complex
```

#### Cyclomatic Complexity
```
1-10: ✅ Simple, easy to test
11-20: ⚠️ Moderate complexity
21-50: ⚠️ High complexity, hard to maintain
> 50: ❌ Very high risk
```

**Calculate:** Count decision points (if, while, for, case, &&, ||, ?)

#### Code Duplication
```
❌ BAD:
def calculate_user_score(user):
    total = 0
    for activity in user.activities:
        if activity.type == 'post':
            total += 10
        elif activity.type == 'comment':
            total += 5
    return total

def calculate_team_score(team):
    total = 0
    for member in team.members:
        for activity in member.activities:
            if activity.type == 'post':
                total += 10
            elif activity.type == 'comment':
                total += 5
    return total

✅ GOOD:
def calculate_score(activities):
    """Reusable score calculation"""
    points = {'post': 10, 'comment': 5}
    return sum(points.get(a.type, 0) for a in activities)

def calculate_user_score(user):
    return calculate_score(user.activities)

def calculate_team_score(team):
    all_activities = [a for m in team.members for a in m.activities]
    return calculate_score(all_activities)
```

---

### Step 3b: Reusability Checklist (HIGH — Check Every Review)

#### Duplication Detection
- [ ] No copy-pasted logic across files (3-strike rule: 3+ occurrences → extract)
- [ ] Utility functions in shared modules (`lib/utils/`), not defined inline
- [ ] Existing shared modules used where applicable (check `lib/`, `shared/`, `packages/`)
- [ ] Magic numbers and repeated constants extracted to `lib/config/constants`

#### Shared Module Quality
- [ ] New shared modules have clear single responsibility
- [ ] Barrel exports used for clean import paths (`index.ts` / `__init__.py`)
- [ ] Shared modules documented (docstring/JSDoc on exported functions)
- [ ] Shared modules have 2+ consumers (no premature abstraction)

#### Folder Convention Compliance
| Category | Expected Location |
|---|---|
| Utilities | `lib/utils/` or `src/lib/utils/` |
| Services (API, DB, auth) | `lib/services/` or `src/lib/services/` |
| Types/DTOs/Enums | `lib/types/` or `src/lib/types/` |
| Config/Constants | `lib/config/` or `src/lib/config/` |
| Shared UI Components | `components/shared/` or `lib/components/` |
| Hooks (React/framework) | `lib/hooks/` or `src/lib/hooks/` |

#### Anti-Patterns to Flag
```
❌ Copy-pasted logic across files → extract to lib/utils/
❌ Inline utility in component/route → move to lib/utils/
❌ Fat class/component mixing concerns → decompose into composable units
❌ Hardcoded values repeated across files → extract to lib/config/constants
❌ Re-implementing stdlib (custom date parsing, string helpers) → use standard library
❌ Functions > 30 lines with extractable sub-logic → decompose
❌ Files importing 0 shared modules → review for reinvention
```

#### Reusability in Review Output
Add a **🟢 Reusability** section to every review report:
```markdown
## 🟢 Reusability
- [Logic] duplicated in [file1] and [file2] → extract to lib/utils/
- [Constant] hardcoded in N files → move to lib/config/constants
- [Function] is inline utility → move to lib/utils/[name]
- ✅ Shared modules used appropriately (no issues found)
```

---

### Step 4: Style and Conventions

#### Naming Conventions

**Python:**
```python
# ✅ GOOD
user_count = 10
USER_API_KEY = "..."
class UserManager:
    def get_user_by_id(self, user_id):
        pass

# ❌ BAD
UserCount = 10  # Should be lowercase
user_api_key = "..."  # Should be uppercase constant
class user_manager:  # Should be PascalCase
    def GetUserById(self, UserId):  # Should be snake_case
        pass
```

**JavaScript/TypeScript:**
```javascript
// ✅ GOOD
const userCount = 10;
const USER_API_KEY = "...";
class UserManager {
    getUserById(userId) {}
}

// ❌ BAD
const UserCount = 10;  // Should be camelCase
const user_api_key = "...";  // Should be camelCase or UPPERCASE
class user_manager {  // Should be PascalCase
    get_user_by_id(user_id) {}  // Should be camelCase
}
```

#### Documentation Requirements

**Functions/Methods:**
```python
# ❌ MISSING DOCS
def process_payment(user, amount):
    # Complex logic...
    return result

# ✅ GOOD DOCS
def process_payment(user: User, amount: Decimal) -> PaymentResult:
    """
    Process a payment for the given user.

    Args:
        user: The user making the payment
        amount: Payment amount in USD (must be positive)

    Returns:
        PaymentResult containing transaction ID and status

    Raises:
        ValueError: If amount is negative or zero
        PaymentError: If payment processing fails

    Example:
        >>> result = process_payment(user, Decimal('99.99'))
        >>> print(result.transaction_id)
        'txn_123456'
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    # Process payment...
    return result
```

**Classes:**
```python
# ✅ GOOD
class UserManager:
    """
    Manages user accounts and authentication.

    This class handles user CRUD operations, authentication,
    and session management.

    Attributes:
        db: Database connection
        cache: Redis cache for sessions

    Example:
        manager = UserManager(db, cache)
        user = manager.get_user_by_email('user@example.com')
    """
```

---

### Step 5: Performance Review

#### Database Queries

**N+1 Query Problem:**
```python
# ❌ BAD (N+1 queries)
users = User.query.all()
for user in users:
    print(user.profile.bio)  # Separate query for each user

# ✅ GOOD (2 queries or 1 with join)
users = User.query.options(joinedload(User.profile)).all()
for user in users:
    print(user.profile.bio)  # Already loaded
```

**Missing Indexes:**
```python
# ⚠️ CHECK: Are frequently queried fields indexed?
# If querying by email often:
class User(db.Model):
    email = db.Column(db.String, index=True)  # ✅ Indexed

# If filtering by status often:
class Order(db.Model):
    status = db.Column(db.String, index=True)  # ✅ Indexed
```

#### Caching Opportunities
```python
# ❌ MISSING CACHE
def get_popular_posts():
    return Post.query.filter_by(featured=True).all()

# ✅ WITH CACHE
@cache.memoize(timeout=300)  # 5 minutes
def get_popular_posts():
    return Post.query.filter_by(featured=True).all()
```

#### Algorithm Efficiency
```python
# ❌ O(n²) - Slow for large lists
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

# ✅ O(n) - Much faster
def find_duplicates(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
```

---

### Step 6: Error Handling

**Proper Exception Handling:**
```python
# ❌ BAD
try:
    result = risky_operation()
except:  # Bare except catches everything!
    pass  # Silent failure

# ✅ GOOD
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise  # Re-raise or handle appropriately
finally:
    cleanup_resources()  # Always execute
```

**Input Validation:**
```python
# ❌ NO VALIDATION
def divide(a, b):
    return a / b  # What if b is 0?

# ✅ WITH VALIDATION
def divide(a: float, b: float) -> float:
    """Divide a by b with validation."""
    if b == 0:
        raise ValueError("Division by zero")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments must be numbers")
    return a / b
```

---

### Step 7: Testing Requirements

**Test Coverage Expectations:**
- **Critical code** (auth, payments): 90-100%
- **Business logic**: 80-90%
- **Utilities**: 70-80%
- **UI components**: 50-70%

**Test Types Needed:**
```python
# Unit tests
def test_calculate_total():
    order = Order(items=[Item(price=10), Item(price=20)])
    assert order.calculate_total() == 30

# Integration tests
def test_create_order_flow():
    user = create_test_user()
    order = create_order(user, items)
    assert order.status == "pending"
    assert order.user_id == user.id

# Edge cases
def test_empty_order():
    order = Order(items=[])
    assert order.calculate_total() == 0
```

---

## Review Checklist Template

### Security ✓
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Authentication/authorization checks present
- [ ] No hardcoded secrets or credentials
- [ ] Input validation implemented
- [ ] Sensitive data properly encrypted/hashed
- [ ] CSRF protection (if applicable)
- [ ] Rate limiting (if applicable)

### Code Quality ✓
- [ ] Files under 800 lines (warn at 500)
- [ ] Functions under 100 lines (warn at 50)
- [ ] Clear, descriptive names
- [ ] No code duplication (DRY)
- [ ] Proper error handling
- [ ] Complexity manageable (< 20 per function)

### Documentation ✓
- [ ] Public functions documented
- [ ] Classes documented
- [ ] Complex logic explained
- [ ] Type hints present (Python/TypeScript)
- [ ] Examples provided where helpful

### Performance ✓
- [ ] No N+1 query problems
- [ ] Appropriate indexes on database fields
- [ ] Caching used where beneficial
- [ ] Efficient algorithms (no O(n²) where avoidable)
- [ ] Resources properly cleaned up

### Testing ✓
- [ ] Unit tests added/updated
- [ ] Integration tests (if applicable)
- [ ] Edge cases covered
- [ ] Tests pass locally
- [ ] Coverage meets requirements

### Best Practices ✓
- [ ] Follows language/framework conventions
- [ ] SOLID principles applied
- [ ] Clean code principles followed
- [ ] Team coding standards met
- [ ] No anti-patterns

---

## Output Format

### Review Summary Template

```markdown
# Code Review: [Feature/PR Name]

## Summary
**Recommendation:** [Approve / Request Changes / Comment]

**Lines Changed:** [number]
**Files Changed:** [number]
**Review Type:** [Quick / Standard / Comprehensive]

## Security Issues

### CRITICAL
- [Issue description]
  - **File:** path/to/file.py:123
  - **Problem:** [Explain the vulnerability]
  - **Fix:** [How to fix it]

### HIGH
[Similar format]

### MEDIUM
[Similar format]

## Quality Issues

### File Size Warnings
- `large_file.py`: 1,234 lines ⚠️ Should refactor

### Complexity Warnings
- `complex_function()`: Cyclomatic complexity 45 ⚠️ Simplify

### Code Duplication
- Functions `calc_a()` and `calc_b()` share 80% code ⚠️ Extract common logic

## Performance Concerns

- [Issue description with file and line]
- [Recommendation]

## Best Practices

- [Suggestion 1]
- [Suggestion 2]

## Action Items

1. [ ] Fix CRITICAL security issue in auth.py:45
2. [ ] Refactor large_file.py (break into modules)
3. [ ] Add input validation to user_controller.py
4. [ ] Improve test coverage for payment module
5. [ ] Add documentation to public API functions

## Positive Highlights

- Excellent test coverage
- Clear variable names
- Good error handling in most places

## Overall Assessment

[Brief summary of code quality and readiness]
```

---

## Language-Specific Guidelines

### Python
- Follow PEP 8
- Use type hints
- Docstrings for public functions
- List comprehensions over loops (when readable)
- Context managers for resources

### JavaScript/TypeScript
- Use `const` by default, `let` when needed, never `var`
- Prefer arrow functions for callbacks
- Use async/await over promises chains
- Destructuring for cleaner code
- TypeScript: Define interfaces/types

### SQL
- Parameterized queries always
- Indexes on foreign keys
- Avoid SELECT *
- Use transactions appropriately

---

## Integration with gald3r

### Creating Tasks from Review Findings

When review finds issues:
1. Create tasks for HIGH/CRITICAL security issues immediately
2. Create refactoring tasks for large files
3. Create bug tasks for logic errors
4. Update TASKS.md with priority

**Example:**
```
Review finds SQL injection → Create CRITICAL task
Review finds 1000-line file → Create refactoring task
Review finds missing tests → Create improvement task
```

---

## Tips for Effective Reviews

### DO
✅ Be specific (line numbers, exact issues)
✅ Explain WHY something is a problem
✅ Suggest concrete solutions
✅ Acknowledge good code
✅ Prioritize issues (critical first)

### DON'T
❌ Be vague ("this looks bad")
❌ Only point out problems (also praise good parts)
❌ Overwhelm with minor issues
❌ Be condescending
❌ Skip security checks

---

## Automation Opportunities

Consider automating:
- Static analysis (pylint, eslint, etc.)
- Security scanning (Bandit, OWASP ZAP)
- Test coverage reporting
- Complexity metrics
- Style checking (Black, Prettier)

Manual review should focus on:
- Business logic correctness
- Architecture decisions
- Complex security scenarios
- User experience implications
- Domain-specific concerns

---

**Remember:** The goal is to improve code quality while maintaining developer morale. Be thorough but constructive.
