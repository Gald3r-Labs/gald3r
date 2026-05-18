# Bug Tracking

## Active Bugs

### Bug ID: BUG-001
- **Title**: Login button not responding to clicks
- **Severity**: Critical
- **Source**: Production
- **Feature Impact**: User Authentication
- **Status**: Closed
- **Task Reference**: Task 015
- **Created**: 2025-10-18
- **Assigned**: Sarah Chen
- **Resolved**: 2025-10-18

**Description**:
Login button on homepage does not respond when clicked. No error messages displayed, no console errors. Affects all users on all browsers.

**Reproduction Steps**:
1. Navigate to homepage (https://app.example.com)
2. Click "Login" button in top-right corner
3. Observe no response

**Expected Behavior**: Login modal should appear with email/password fields

**Actual Behavior**: Button click has no visual or functional effect

**Root Cause**: Event listener removed during refactoring in commit abc123

**Resolution**: Restored click event listener in auth.js, added unit test to verify listener attachment

**Resolution Date**: 2025-10-18 17:00 UTC

---

### Bug ID: BUG-002
- **Title**: Shopping cart total calculation incorrect
- **Severity**: High
- **Source**: User Reported
- **Feature Impact**: Shopping Cart, Checkout
- **Status**: Fixing
- **Task Reference**: Task 017
- **Created**: 2025-10-19
- **Assigned**: Mike Johnson

**Description**:
Shopping cart displays incorrect total when items have discounts applied. Subtotal is correct, but final total doesn't reflect discount percentage properly.

**Reproduction Steps**:
1. Add item with price $100 to cart
2. Apply 20% discount code
3. Observe total shows $95 instead of $80

**Expected Behavior**: Total should be $80 ($100 - 20% = $80)

**Actual Behavior**: Total shows $95 (appears to calculate 5% discount instead of 20%)

**Environment**:
- Browser: Chrome 118, Firefox 119
- OS: Windows 11, macOS 14
- Affects all users

**Investigation Notes**:
- Discount calculation logic in cart.js line 142
- Appears to be using wrong variable for discount percentage
- Fix in progress, testing locally

---

### Bug ID: BUG-003
- **Title**: Product images not loading on mobile
- **Severity**: Medium
- **Source**: Testing
- **Feature Impact**: Product Catalog
- **Status**: Investigating
- **Task Reference**: Task 018
- **Created**: 2025-10-19
- **Assigned**: Lisa Park

**Description**:
Product images fail to load on mobile devices (iOS and Android). Desktop works fine. Images show broken image icon.

**Reproduction Steps**:
1. Open product catalog on mobile device
2. Scroll through products
3. Observe images not loading (broken icon)

**Expected Behavior**: Product images should load and display properly

**Actual Behavior**: Broken image icons displayed

**Environment**:
- Mobile: iOS 17 (Safari), Android 13 (Chrome)
- Desktop: Works fine on all browsers
- Image URLs are correct (verified in network tab)

**Investigation Status**:
- Checking image CDN configuration
- Testing different image sizes
- Reviewing mobile-specific CSS

---

### Bug ID: BUG-004
- **Title**: Email notifications delayed by 2+ hours
- **Severity**: Medium
- **Source**: Production
- **Feature Impact**: Email Notifications
- **Status**: Open
- **Task Reference**: Task 019
- **Created**: 2025-10-19
- **Assigned**: Unassigned

**Description**:
Order confirmation emails are delayed by 2-3 hours. Users expect immediate confirmation but emails arrive much later.

**Reproduction Steps**:
1. Place order
2. Wait for confirmation email
3. Email arrives 2-3 hours later

**Expected Behavior**: Email should arrive within 1-2 minutes

**Actual Behavior**: Email delayed by 2-3 hours

**Environment**:
- Email service: SendGrid
- Affects all users
- Started occurring on 2025-10-18

**Notes**:
- May be SendGrid rate limiting
- Need to check email queue
- Possible infrastructure issue

---

### Bug ID: BUG-005
- **Title**: Search returns no results for valid queries
- **Severity**: High
- **Source**: User Reported
- **Feature Impact**: Product Search
- **Status**: Open
- **Task Reference**: Task 020
- **Created**: 2025-10-19
- **Assigned**: Unassigned

**Description**:
Product search returns "No results found" for queries that should return products. Affects specific product categories.

**Reproduction Steps**:
1. Enter search query "laptop"
2. Click search
3. Observe "No results found" despite having 15 laptops in catalog

**Expected Behavior**: Should return 15 laptop products

**Actual Behavior**: Returns no results

**Environment**:
- Affects all users
- Started after search index rebuild on 2025-10-19
- Other search terms work fine

**Notes**:
- Possible search index corruption
- May need to rebuild index
- Urgent - affects sales

## Closed Bugs

### Bug ID: BUG-001
- **Title**: Login button not responding to clicks
- **Severity**: Critical
- **Resolved**: 2025-10-18
- **Resolution Time**: 2 hours 45 minutes
- **Root Cause**: Event listener removed during refactoring
- **Fix**: Restored event listener, added unit test

---

## Bug Statistics

**Total Bugs**: 5  
**Active**: 4  
**Closed**: 1

**By Severity**:
- Critical: 0 active, 1 closed
- High: 2 active
- Medium: 2 active
- Low: 0 active

**By Source**:
- User Reported: 3
- Production: 2
- Testing: 1
- Development: 0

**By Status**:
- Open: 2
- Investigating: 1
- Fixing: 1
- Testing: 0
- Closed: 1

**Average Resolution Time**: 2.75 hours (1 bug resolved)

---

**Last Updated**: 2025-10-19 11:45 AM

