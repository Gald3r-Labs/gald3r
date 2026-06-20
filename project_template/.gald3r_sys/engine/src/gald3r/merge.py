"""Cross-project item merge keyed on the stable uuid (T522 AC5).

The display id (`T###` / `BUG-###`) is repo-local and collides on merge; the `uuid` (T522
data-model) is the durable identity. This module is the data-model-USE half of safe
merge/absorb/split — a PURE algorithm over item dicts (no file IO, no host assumptions);
the caller loads the items, applies the plan, and persists + rewrites references.

Merge rule (documented contract):
  1. ``incoming.uuid`` already present in the target  -> **SKIP** (same item; never duplicated,
     never renumbered).
  2. ``incoming.uuid`` new AND its display id is free in the target -> **IMPORT as-is**.
  3. ``incoming.uuid`` new AND its display id collides with a *different-uuid* target item ->
     **RENUMBER the incoming display id** to the next free id (the target's ids are never
     touched), then import. The (old -> new) remap is reported so the caller can rewrite the
     incoming items' cross-references (e.g. ``dependencies``).

An incoming item with no uuid is treated as a fresh item (rule 2/3) — it can never false-merge
onto a target item, satisfying "zero false-merge".
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional


def _num(value: Any) -> Optional[int]:
    m = re.search(r"\d+", str(value))
    return int(m.group()) if m else None


def _fmt_like(n: int, like: Any) -> Any:
    """Format a new numeric id to match the shape of an existing display id:
    bare int -> int; ``BUG-007`` -> ``BUG-008`` (prefix + zero-pad preserved)."""
    s = str(like)
    m = re.match(r"^(.*?)(\d+)\s*$", s)
    if m and m.group(1):                       # has a non-numeric prefix, e.g. "BUG-"
        pad = len(m.group(2))
        return f"{m.group(1)}{n:0{pad}d}"
    if isinstance(like, int):
        return n
    return str(n)


def plan_merge(target_items: List[Dict[str, Any]],
               incoming_items: List[Dict[str, Any]],
               *, id_key: str = "id", uuid_key: str = "uuid") -> Dict[str, Any]:
    """Return a non-destructive merge plan. Does NOT mutate inputs.

    Result:
      ``imported``   - incoming items to add (renumbered copies where rule 3 applied)
      ``skipped``    - incoming items already present by uuid (rule 1)
      ``renumbered`` - list of {uuid, old_id, new_id} for rule-3 items
      ``id_remap``   - {old_display_id: new_display_id} for cross-reference rewriting
    """
    target_uuids = {it.get(uuid_key) for it in target_items if it.get(uuid_key)}
    used_nums = {n for it in target_items if (n := _num(it.get(id_key))) is not None}

    imported: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    renumbered: List[Dict[str, Any]] = []
    id_remap: Dict[Any, Any] = {}

    next_num = (max(used_nums) + 1) if used_nums else 1
    for inc in incoming_items:
        u = inc.get(uuid_key)
        if u and u in target_uuids:
            skipped.append(inc)                                   # rule 1: same item
            continue
        iid = inc.get(id_key)
        inum = _num(iid)
        if inum is not None and inum in used_nums:                # rule 3: display-id collision
            new_id = _fmt_like(next_num, iid)
            used_nums.add(next_num)
            next_num += 1
            renumbered.append({"uuid": u, "old_id": iid, "new_id": new_id})
            id_remap[iid] = new_id
            imported.append({**inc, id_key: new_id})
        else:                                                     # rule 2: import as-is
            if inum is not None:
                used_nums.add(inum)
            imported.append(dict(inc))
    return {"imported": imported, "skipped": skipped,
            "renumbered": renumbered, "id_remap": id_remap}


def remap_refs(refs: List[Any], id_remap: Dict[Any, Any]) -> List[Any]:
    """Rewrite a list of display-id references (e.g. ``dependencies``) through an id_remap,
    preserving order and any refs that were not renumbered."""
    return [id_remap.get(r, r) for r in refs]


class MergeSystem:
    """Thin facade wrapper (``g.merge``). Pure planning over item collections — the caller
    supplies items (e.g. from `g.tasks.list()` / `g.bugs.list()` of two repos) and persists
    the plan. Persistence/absorption execution is intentionally out of scope here."""

    def __init__(self, config: Any = None):
        self.config = config

    def plan(self, target_items, incoming_items, *, id_key="id", uuid_key="uuid"):
        return plan_merge(target_items, incoming_items, id_key=id_key, uuid_key=uuid_key)

    @staticmethod
    def remap_refs(refs, id_remap):
        return remap_refs(refs, id_remap)
