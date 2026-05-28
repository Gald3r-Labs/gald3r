# Bug Classification Guide

## Overview

This guide provides detailed definitions for bug severity levels, source attribution, and status lifecycle in the gald3r QA system.

## Severity Levels

### Critical
**Definition**: System crashes, data loss, security vulnerabilities, or complete feature failure affecting all users.

**Characteristics:**
- Blocks core functionality
- Affects all or most users
- No workaround available
- Immediate fix required
- Production deployment should be halted

**Examples:**
- Application crashes on startup
- Database corruption
- Security vulnerability (SQL injection, XSS)
- Payment processing failure
- Data loss on save
- Authentication completely broken

**Response Time:** Immediate (< 1 hour)  
**Fix Timeline:** Same day  
**Priority:** Drop everything

### High
**Definition**: Major feature failures or performance degradation >50% affecting many users.

**Characteristics:**
- Significant feature impairment
- Affects many users
- Workaround exists but difficult
- Fix needed within 24-48 hours
- Impacts user experience significantly

**Examples:**
- Major feature not working (e.g., search returns no results)
- Performance degradation (5x slower than normal)
- Important button not responding
- Email notifications not sending
- Reports showing incorrect data
- Mobile app crashes on specific action

**Response Time:** Within 4 hours  
**Fix Timeline:** 1-2 days  
**Priority:** High, schedule immediately

### Medium
**Definition**: Minor feature issues or usability problems affecting some users.

**Characteristics:**
- Feature works but with issues
- Affects some users or specific scenarios
- Workaround available
- Fix needed within 1 week
- Annoying but not blocking

**Examples:**
- UI element misaligned
- Validation message unclear
- Feature works but slow (2x normal)
- Minor calculation error
- Inconsistent behavior across browsers
- Missing error message
- Tooltip doesn't appear

**Response Time:** Within 24 hours  
**Fix Timeline:** 3-7 days  
**Priority:** Medium, schedule in sprint

### Low
**Definition**: Cosmetic issues, enhancement requests, or minor inconveniences.

**Characteristics:**
- Doesn't affect functionality
- Affects very few users
- Easy workaround
- Fix can wait
- Nice to have, not need to have

**Examples:**
- Typo in UI text
- Color slightly off
- Icon not perfectly centered
- Console warning (no user impact)
- Minor formatting issue
- Unnecessary whitespace
- Outdated help text

**Response Time:** When convenient  
**Fix Timeline:** Next release  
**Priority:** Low, backlog

## Source Attribution

### User Reported
**Definition**: Issues reported by end users or stakeholders.

**Characteristics:**
- Discovered in production
- Real-world usage scenario
- May lack technical details
- High priority (affects actual users)

**Examples:**
- Customer support ticket
- User feedback form
- Social media report
- Email to support
- In-app feedback

**Handling:**
- Thank the user
- Reproduce the issue
- Gather additional details
- Keep user informed of progress
- Notify when fixed

### Development
**Definition**: Bugs discovered during feature development.

**Characteristics:**
- Found before production
- Technical context available
- Often caught early
- Lower urgency (not affecting users yet)

**Examples:**
- Developer notices issue while coding
- Code review identifies problem
- Local testing reveals bug
- Integration testing failure
- Peer review feedback

**Handling:**
- Fix before merging
- Add tests to prevent recurrence
- Document for team learning
- May not need BUGS.md entry if fixed immediately

### Testing
**Definition**: Issues found during QA or automated testing.

**Characteristics:**
- Caught in testing phase
- Detailed reproduction steps
- Test environment context
- Prevents production issues

**Examples:**
- QA tester finds issue
- Automated test failure
- Regression testing catches bug
- Performance test reveals issue
- Security scan identifies vulnerability

**Handling:**
- Block deployment if critical/high
- Create detailed bug report
- Retest after fix
- Update test suite
- Track in quality metrics

### Production
**Definition**: Live environment issues requiring immediate attention.

**Characteristics:**
- Affecting real users now
- Highest urgency
- May need hotfix
- Requires monitoring

**Examples:**
- Production monitoring alert
- User complaints spike
- Error rate increase
- Performance degradation
- Service outage

**Handling:**
- Immediate response
- Assess impact
- Deploy hotfix if needed
- Root cause analysis
- Post-mortem review

## Status Lifecycle

### Open
**Definition**: Bug reported, not yet being worked on.

**Next Steps:**
- Triage and prioritize
- Assign to developer
- Gather additional information
- Move to Investigating

**Duration:** Minutes to hours (critical), hours to days (others)

### Investigating
**Definition**: Actively researching root cause.

**Activities:**
- Reproduce the issue
- Analyze logs and data
- Review related code
- Identify root cause
- Plan fix approach

**Next Steps:** Move to Fixing once root cause identified

**Duration:** Hours to days depending on complexity

### Fixing
**Definition**: Actively implementing the fix.

**Activities:**
- Write fix code
- Add/update tests
- Code review
- Update documentation
- Prepare for deployment

**Next Steps:** Move to Testing once fix implemented

**Duration:** Hours to days depending on complexity

### Testing
**Definition**: Verifying the fix works.

**Activities:**
- Test original reproduction steps
- Run regression tests
- Verify in staging environment
- Get QA approval
- Prepare for production deployment

**Next Steps:** Move to Closed if tests pass, back to Fixing if issues found

**Duration:** Hours to 1 day

### Closed
**Definition**: Bug fixed, verified, and deployed.

**Final Steps:**
- Deploy to production
- Monitor for 24-48 hours
- Notify stakeholders
- Update documentation
- Archive bug record

**Reopening:** If bug recurs, reopen with new information

## Classification Decision Tree

```
Is the system completely unusable?
├─ Yes → CRITICAL
└─ No → Is a major feature broken?
    ├─ Yes → HIGH
    └─ No → Does it affect functionality?
        ├─ Yes → MEDIUM
        └─ No → LOW (cosmetic)
```

## Common Misclassifications

### Over-Classification
❌ **Incorrect**: Typo marked as Critical  
✅ **Correct**: Typo is Low severity

❌ **Incorrect**: UI alignment issue marked as High  
✅ **Correct**: UI alignment is Medium or Low

❌ **Incorrect**: Feature request marked as bug  
✅ **Correct**: Feature requests go in planning, not bugs

### Under-Classification
❌ **Incorrect**: Data loss marked as Medium  
✅ **Correct**: Data loss is always Critical

❌ **Incorrect**: Security vulnerability marked as Low  
✅ **Correct**: Security issues are Critical or High

❌ **Incorrect**: Production outage marked as High  
✅ **Correct**: Outages are Critical

## Best Practices

1. **Be Honest**: Don't inflate severity for attention
2. **Be Specific**: Provide clear reproduction steps
3. **Be Consistent**: Use same criteria across team
4. **Be Responsive**: Update status as work progresses
5. **Be Thorough**: Document root cause and fix

## Summary

Proper bug classification ensures:
- ✅ Right priority assignment
- ✅ Appropriate response time
- ✅ Effective resource allocation
- ✅ Clear communication
- ✅ Quality metrics accuracy

Use this guide to maintain consistent, accurate bug classification across your team.

