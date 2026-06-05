"""The prompt/judgment layer — gald3r's centralized library of LLM-judgment assets.

The deterministic systems (`systems/*.py`) are the 74% that became code. This is the
other side: the reusable *reasoning* — persona voice, agent role briefs, review
rubrics, planning/design playbooks, marketing voice — that genuinely needs an LLM and
so stays as prompts. Centralizing it here means ONE canonical copy (not duplicated
across `.claude/` + `.cursor/` + 34 platforms) that every surface can fetch.

Critical boundary, identical to the rest of the core: this module **serves** prompts;
it never **executes** them. No LLM calls. The caller (a Mode-A IDE harness, or the
future Mode-B `pipeline/`) runs the returned text. That keeps Mode A pure and lets the
Mode-B harness be "just another caller."

Assets live as markdown under `prompts/assets/<id>.md` with frontmatter:

    ---
    id: role.code_reviewer
    kind: persona | role | rubric | playbook | voice | rule
    title: "Gald3r Code Reviewer"
    inputs: [diff_summary]          # optional ${slot} names
    tier: slim
    source: agents/g-agnt-code-reviewer.md   # provenance back to the markdown
    version: 1
    ---
    <body — judgment only; ${slot} marks an input>
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r.store import split_doc

_ASSETS_DIR = Path(__file__).parent / "assets"
_SLOT = re.compile(r"\$\{(\w+)\}")


@dataclass
class PromptAsset:
    id: str
    kind: str
    title: str
    body: str
    inputs: List[str]
    tier: str
    source: str
    version: int
    path: Path

    def render(self, **values: Any) -> str:
        """Substitute declared ${inputs}. Targeted replace (not str.format) so the
        abundant literal `{...}` / `$` in bodies is left untouched. Missing input → error."""
        declared = set(self.inputs)
        missing = [k for k in declared if k not in values]
        if missing:
            raise ValueError(f"prompt {self.id} missing input(s): {', '.join(sorted(missing))}")

        def repl(m: "re.Match[str]") -> str:
            name = m.group(1)
            if name not in declared:
                return m.group(0)         # not a declared slot — leave literal
            return str(values[name])

        return _SLOT.sub(repl, self.body)

    def meta(self) -> Dict[str, Any]:
        return {"id": self.id, "kind": self.kind, "title": self.title,
                "inputs": self.inputs, "tier": self.tier, "source": self.source,
                "version": self.version}


class PromptLibrary:
    """Loads and serves the prompt assets shipped with the package."""

    def __init__(self, assets_dir: Optional[Path] = None):
        self.dir = Path(assets_dir or _ASSETS_DIR)

    def _files(self) -> List[Path]:
        return sorted(self.dir.glob("*.md")) if self.dir.exists() else []

    def _load(self, path: Path) -> Optional[PromptAsset]:
        fm, body = split_doc(path.read_text(encoding="utf-8-sig"))
        pid = fm.get("id") or path.stem
        if not body.strip():
            return None
        inputs = fm.get("inputs") or []
        if isinstance(inputs, str):
            inputs = [inputs]
        return PromptAsset(
            id=str(pid), kind=str(fm.get("kind", "prompt")),
            title=str(fm.get("title", pid)), body=body.strip(),
            inputs=[str(x) for x in inputs], tier=str(fm.get("tier", "slim")),
            source=str(fm.get("source", "")), version=int(fm.get("version", 1) or 1),
            path=path,
        )

    def list(self, kind: Optional[str] = None) -> List[PromptAsset]:
        assets = [a for a in (self._load(p) for p in self._files()) if a]
        if kind:
            assets = [a for a in assets if a.kind == kind]
        return sorted(assets, key=lambda a: a.id)

    def get(self, prompt_id: str) -> Optional[PromptAsset]:
        return next((a for a in self.list() if a.id == prompt_id), None)

    def render(self, prompt_id: str, **values: Any) -> str:
        a = self.get(prompt_id)
        if not a:
            raise KeyError(f"no prompt asset '{prompt_id}' (have: "
                           f"{', '.join(x.id for x in self.list())})")
        return a.render(**values)

    def ids(self) -> List[str]:
        return [a.id for a in self.list()]
