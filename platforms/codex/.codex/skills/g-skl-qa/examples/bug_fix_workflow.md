# Bug Fix Workflow Example

## Complete Lifecycle: BUG-002 - Shopping Cart Total Calculation

This document shows the complete lifecycle of a bug from discovery through resolution.

---

## Phase 1: Discovery (Day 1 - 10:00 AM)

### Initial Report
**Source**: User Reported (Customer Support Ticket #1234)

**User Report**:
> "I applied a 20% discount code to my $100 order, but the total shows $95 instead of $80. The math doesn't add up!"

**Support Agent Notes**:
- Customer: Jane Smith
- Order ID: ORD-5678
- Discount Code: SAVE20
- Expected Total: $80
- Actual Total: $95
- Browser: Chrome 118
- OS: Windows 11

---

## Phase 2: Bug Creation (Day 1 - 10:15 AM)

### BUGS.md Entry Created

```markdown
### Bug ID: BUG-002
- **Title**: Shopping cart total calculation incorrect
- **Severity**: High
- **Source**: User Reported
- **Feature Impact**: Shopping Cart, Checkout
- **Status**: Open
- **Task Reference**: Task 017
- **Created**: 2025-10-19
- **Assigned**: Unassigned

**Description**:
Shopping cart displays incorrect total when items have discounts applied.
Subtotal is correct, but final total doesn't reflect discount percentage properly.

**Reproduction Steps**:
1. Add item with price $100 to cart
2. Apply 20% discount code
3. Observe total shows $95 instead of $80

**Expected Behavior**: Total should be $80 ($100 - 20% = $80)
**Actual Behavior**: Total shows $95
```

### Task File Created

**File**: `.gald3r/tasks/task017_fix_cart_calculation.md`

```yaml
---
id: 17
title: '[BUG] Fix shopping cart total calculation'
type: bug_fix
status: pending
priority: high
feature: Shopping Cart
subsystems: [cart, checkout, pricing]
project_context: 'Resolves calculation error affecting customer purchases'
bug_reference: BUG-002
severity: high
source: user_reported
reproduction_steps: '1. Add $100 item\n2. Apply 20% discount\n3. Total shows $95 not $80'
expected_behavior: 'Total should be $80 ($100 - 20%)'
actual_behavior: 'Total shows $95 (5% discount instead of 20%)'
dependencies: []
---
```

### TASKS.md Updated

```markdown
- [ ] Task 017: [BUG] Fix shopping cart total calculation
```

---

## Phase 3: Triage (Day 1 - 10:30 AM)

### Bug Review Meeting

**Attendees**: Product Manager, Tech Lead, QA Lead

**Discussion**:
- Affects all users with discount codes
- High priority - impacts revenue
- Assign to Mike Johnson (cart expert)
- Target fix: Within 24 hours

**Decisions**:
- ✅ Severity confirmed: High
- ✅ Assigned: Mike Johnson
- ✅ Priority: P1 (fix in current sprint)
- ✅ Status: Open → Investigating

### Updates Applied

**BUGS.md**:
```markdown
- **Status**: Investigating
- **Assigned**: Mike Johnson
```

**TASKS.md**:
```markdown
- [🔄] Task 017: [BUG] Fix shopping cart total calculation
```

**Task File**:
```yaml
status: in-progress
```

---

## Phase 4: Investigation (Day 1 - 11:00 AM - 2:00 PM)

### Developer Investigation

**11:00 AM - Reproduction**:
- ✅ Bug reproduced locally
- ✅ Affects all discount codes
- ✅ Pattern identified: shows 5% discount regardless of actual percentage

**11:30 AM - Code Review**:
```javascript
// cart.js line 142 - FOUND THE BUG!
function calculateTotal(subtotal, discountCode) {
  const discount = getDiscountPercentage(discountCode);
  // BUG: Using wrong variable!
  const discountAmount = subtotal * (defaultDiscount / 100);  // ❌ WRONG
  return subtotal - discountAmount;
}
```

**Root Cause Identified**:
- Variable name error: using `defaultDiscount` (5%) instead of `discount` (actual percentage)
- Introduced in commit xyz789 during refactoring
- Code review missed this typo

**12:00 PM - Fix Development**:
```javascript
// FIXED VERSION
function calculateTotal(subtotal, discountCode) {
  const discount = getDiscountPercentage(discountCode);
  const discountAmount = subtotal * (discount / 100);  // ✅ CORRECT
  return subtotal - discountAmount;
}
```

**1:00 PM - Unit Test Created**:
```javascript
test('applies 20% discount correctly', () => {
  const subtotal = 100;
  const discountCode = 'SAVE20';
  const total = calculateTotal(subtotal, discountCode);
  expect(total).toBe(80);  // Should be $80, not $95
});
```

**2:00 PM - Code Review**:
- Fix reviewed by Sarah Chen
- Approved
- Ready for testing

### Status Update

**BUGS.md**:
```markdown
- **Status**: Fixing
- **Root Cause**: Variable name error in cart.js line 142
- **Fix**: Use correct discount variable instead of defaultDiscount
```

---

## Phase 5: Testing (Day 1 - 2:30 PM - 4:00 PM)

### QA Testing

**2:30 PM - Deployed to Staging**:
- Fix deployed to staging environment
- Automated tests run: ✅ All passing

**3:00 PM - Manual Testing**:

**Test Case 1**: 20% Discount
- Item: $100
- Code: SAVE20
- Expected: $80
- Actual: $80 ✅

**Test Case 2**: 10% Discount
- Item: $50
- Code: SAVE10
- Expected: $45
- Actual: $45 ✅

**Test Case 3**: 50% Discount
- Item: $200
- Code: HALF OFF
- Expected: $100
- Actual: $100 ✅

**Test Case 4**: Multiple Items
- Items: $100 + $50 = $150
- Code: SAVE20
- Expected: $120
- Actual: $120 ✅

**3:30 PM - Regression Testing**:
- Cart without discount: ✅ Works
- Cart with multiple items: ✅ Works
- Checkout flow: ✅ Works
- Order confirmation: ✅ Works

**4:00 PM - QA Approval**:
- ✅ All tests passed
- ✅ No regressions found
- ✅ Ready for production

### Status Update

**BUGS.md**:
```markdown
- **Status**: Testing → Closed (pending deployment)
```

**TASKS.md**:
```markdown
- [✅] Task 017: [BUG] Fix shopping cart total calculation
```

---

## Phase 6: Deployment (Day 1 - 4:30 PM)

### Production Deployment

**4:30 PM - Deployed to Production**:
- Fix deployed via standard deployment process
- Monitoring dashboards active
- Support team notified

**4:45 PM - Verification**:
- Production smoke tests: ✅ Passed
- Real user transactions: ✅ Working correctly
- Error rate: 0%

**5:00 PM - Customer Notification**:
- Original customer (Jane Smith) notified
- Support ticket #1234 updated
- Offered apology discount code

---

## Phase 7: Closure (Day 1 - 5:30 PM)

### Final Updates

**BUGS.md**:
```markdown
### Bug ID: BUG-002
- **Title**: Shopping cart total calculation incorrect
- **Severity**: High
- **Source**: User Reported
- **Status**: Closed
- **Resolved**: 2025-10-19 17:00 UTC
- **Resolution Time**: 7 hours
- **Root Cause**: Variable name error in discount calculation
- **Fix**: Corrected variable reference in cart.js
```

**Task File**:
```yaml
status: completed
completed_date: '2025-10-19'
```

**TASKS.md**:
```markdown
- [✅] Task 017: [BUG] Fix shopping cart total calculation
```

---

## Phase 8: Post-Mortem (Day 2 - 10:00 AM)

### Lessons Learned Meeting

**What Went Well**:
- ✅ Bug reproduced quickly
- ✅ Root cause identified in 3 hours
- ✅ Fix was simple and clean
- ✅ Comprehensive testing prevented regressions
- ✅ Fast resolution (7 hours total)

**What Could Be Improved**:
- ❌ Code review missed the typo
- ❌ Unit tests didn't catch this initially
- ❌ Should have had better variable naming

**Action Items**:
1. Add more discount calculation tests
2. Improve code review checklist
3. Consider using TypeScript for type safety
4. Add automated discount validation tests
5. Review all similar calculation code

**Prevention Strategy**:
- Better variable naming conventions
- More comprehensive test coverage
- Stricter code review process
- Automated tests for all discount scenarios

---

## Metrics Summary

**Timeline**:
- Discovery: Day 1, 10:00 AM
- Triage: Day 1, 10:30 AM
- Investigation Start: Day 1, 11:00 AM
- Root Cause Found: Day 1, 12:00 PM
- Fix Developed: Day 1, 2:00 PM
- Testing Complete: Day 1, 4:00 PM
- Deployed: Day 1, 4:30 PM
- Verified: Day 1, 5:00 PM
- **Total Time**: 7 hours

**Effort**:
- Investigation: 3 hours
- Fix Development: 2 hours
- Testing: 1.5 hours
- Deployment: 0.5 hours
- **Total Effort**: 7 hours

**Impact**:
- Users Affected: All users with discount codes
- Transactions Affected: Estimated 50-100
- Revenue Impact: Minimal (users still purchased)
- Customer Satisfaction: 1 complaint, resolved

**Quality Metrics**:
- Severity: High
- Resolution Time: 7 hours (Target: <24 hours) ✅
- First Time Fix: Yes ✅
- Regression: No ✅
- Customer Impact: Low (caught early)

---

## Documentation

### Code Comments Added
```javascript
/**
 * Calculates cart total with discount applied
 * @param {number} subtotal - Cart subtotal before discount
 * @param {string} discountCode - Discount code to apply
 * @returns {number} Total after discount
 * 
 * Note: Fixed in BUG-002 - ensure using correct discount variable
 */
function calculateTotal(subtotal, discountCode) {
  const discount = getDiscountPercentage(discountCode);
  const discountAmount = subtotal * (discount / 100);
  return subtotal - discountAmount;
}
```

### Test Documentation Updated
- Added discount calculation test suite
- Documented edge cases
- Added regression test for BUG-002

### Knowledge Base Updated
- Added troubleshooting guide for discount issues
- Documented common calculation errors
- Added to onboarding checklist

---

## Conclusion

**Bug Resolution**: Successful ✅  
**Process Followed**: Complete ✅  
**Quality Maintained**: High ✅  
**Customer Satisfaction**: Restored ✅  
**Lessons Learned**: Documented ✅  
**Prevention Measures**: Implemented ✅

This bug demonstrates a complete, successful bug fix workflow from discovery through resolution and post-mortem analysis.

