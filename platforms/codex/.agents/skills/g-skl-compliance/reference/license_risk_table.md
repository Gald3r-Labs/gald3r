---
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---
# License Risk Table — g-skl-compliance

Canonical license → risk tier mapping for gald3r compliance scanning.

## Risk Tiers

| Tier | Meaning | Hook behavior |
|------|---------|---------------|
| `ok` | Permissive — use freely in any project | PASS |
| `warn` | Weak copyleft or unknown — review before release | WARN |
| `block` | Strong copyleft — cannot distribute as proprietary | FAIL |

---

## OK (Permissive)

| License | SPDX ID | Notes |
|---------|---------|-------|
| MIT | MIT | Most common permissive license |
| Apache 2.0 | Apache-2.0 | Patent grant included |
| BSD 2-Clause | BSD-2-Clause | Simplified BSD |
| BSD 3-Clause | BSD-3-Clause | Modified BSD |
| ISC | ISC | Functionally equivalent to MIT |
| Zero-Clause BSD | 0BSD | Public domain equivalent |
| Unlicense | Unlicense | Explicit public domain dedication |
| CC0 1.0 | CC0-1.0 | Creative Commons public domain |
| Boost Software License | BSL-1.0 | Permissive |
| zLib | Zlib | Permissive |
| Python Software Foundation | PSF-2.0 | Python standard library |

---

## WARN (Weak Copyleft — Review Required)

| License | SPDX ID | Notes |
|---------|---------|-------|
| LGPL 2.0 | LGPL-2.0-only | Dynamic linking OK; static may require source |
| LGPL 2.1 | LGPL-2.1-only | Most common LGPL; Java/Android use common |
| LGPL 3.0 | LGPL-3.0-only | Same as LGPL 2.1 + compatibility with GPL 3 |
| MPL 2.0 | MPL-2.0 | File-level copyleft; modifications must stay MPL |
| CDDL 1.0 | CDDL-1.0 | File-level copyleft; GPL-incompatible |
| EPL 1.0 | EPL-1.0 | Eclipse — file-level copyleft |
| EPL 2.0 | EPL-2.0 | Eclipse — adds secondary license option |
| EUPL 1.2 | EUPL-1.2 | EU Public License — copyleft with compatibility list |
| CDLA-Permissive-2.0 | CDLA-Permissive-2.0 | Data license — review for data assets |
| Unknown / No SPDX | — | No license declared — flag for legal review |

---

## BLOCK (Strong Copyleft — Cannot Distribute as Proprietary)

| License | SPDX ID | Notes |
|---------|---------|-------|
| GPL 2.0 | GPL-2.0-only | Copyleft infects the whole binary |
| GPL 2.0+ | GPL-2.0-or-later | Same effect |
| GPL 3.0 | GPL-3.0-only | Stricter + anti-tivoization |
| GPL 3.0+ | GPL-3.0-or-later | Same effect |
| AGPL 3.0 | AGPL-3.0-only | GPL 3 + network use triggers copyleft (SaaS risk) |
| AGPL 3.0+ | AGPL-3.0-or-later | Same effect |
| SSPL 1.0 | SSPL-1.0 | MongoDB — service offering triggers entire stack |
| BUSL 1.1 | BUSL-1.1 | Business Source — time-limited production restriction |
| Commons Clause | — | Not an OSI license; adds proprietary restriction |

---

## Special Cases

- **Dual-licensed** packages (e.g., `MIT OR Apache-2.0`): use the more permissive tier.
- **Commercial license available**: flag as `warn` with note to check if commercial license is needed.
- **No license file**: treat as `warn` / unknown — contact upstream maintainer.
- **Custom license**: human review required — flag as `warn`.

---

## Notes for Proprietary Distribution

If your project is distributed to end-users (binary, SaaS, or otherwise):
- `block` licenses require source release or license exception from the copyright holder
- `warn` licenses require compliance review — consult legal counsel for production deployments
- `ok` licenses impose no restrictions beyond attribution requirements

For internal tools only (not distributed outside your org), `warn` tier licenses are generally acceptable without special compliance steps.
