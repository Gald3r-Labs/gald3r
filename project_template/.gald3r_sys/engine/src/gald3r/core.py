"""The Gald3r facade — the single entry object. Every surface (CLI, MCP, HTTP)
goes through this. Adding a system = adding a property here + a module under
`systems/`. Tier-gated: a property may refuse to activate below its tier.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from gald3r.config import Config
from gald3r.systems.tasks import TaskSystem
from gald3r.systems.goals import GoalSystem
from gald3r.systems.bugs import BugSystem
from gald3r.systems.features import FeatureSystem
from gald3r.systems.prds import PrdSystem
from gald3r.systems.ideas import IdeaSystem
from gald3r.systems.vocab import VocabSystem
from gald3r.systems.constraints import ConstraintSystem
from gald3r.systems.subsystems import SubsystemSystem
from gald3r.systems.vault import VaultSystem
from gald3r.systems.release import ReleaseSystem
from gald3r.prompts import PromptLibrary


class Gald3r:
    def __init__(self, root: Optional[Path] = None):
        self.config = Config(root)

    @property
    def tier(self) -> str:
        return self.config.tier

    @property
    def tasks(self) -> TaskSystem:
        return TaskSystem(self.config)

    @property
    def goals(self) -> GoalSystem:
        return GoalSystem(self.config)

    @property
    def bugs(self) -> BugSystem:
        return BugSystem(self.config)

    @property
    def features(self) -> FeatureSystem:
        return FeatureSystem(self.config)

    @property
    def prds(self) -> PrdSystem:
        return PrdSystem(self.config)

    @property
    def ideas(self) -> IdeaSystem:
        return IdeaSystem(self.config)

    @property
    def vocab(self) -> VocabSystem:
        return VocabSystem(self.config)

    @property
    def constraints(self) -> ConstraintSystem:
        return ConstraintSystem(self.config)

    @property
    def subsystems(self) -> SubsystemSystem:
        return SubsystemSystem(self.config)

    @property
    def vault(self) -> VaultSystem:
        return VaultSystem(self.config)

    @property
    def session(self) -> "SessionSystem":
        """Persistent agent session-state + insights (T601) — operational memory
        that survives context resets; file-backed under `.gald3r/sessions/`. Distinct
        from the vault (permanent knowledge)."""
        from gald3r.systems.session import SessionSystem
        return SessionSystem(self.config)

    @property
    def inbox(self) -> "InboxSystem":
        """Inbox intake — ingest staged task/bug drafts from the gitignored inbox
        folders into live tracked state. Absorbs custom_scripts/hot_inbox_intake.ps1."""
        from gald3r.systems.inbox import InboxSystem
        return InboxSystem(self.config)

    @property
    def doctor(self) -> "DoctorSystem":
        """Read-only health check across the systems. Absorbs the deterministic half of
        custom_scripts/gald3r_system_test.ps1 (the git/subprocess checks stay external)."""
        from gald3r.systems.doctor import DoctorSystem
        return DoctorSystem(self)

    @property
    def tiers(self) -> "TierSystem":
        """Product-tier show/set on `.gald3r/.identity` (the `g.tier` string property above
        is the bare value). Absorbs the pure half of custom_scripts/tier_sync.ps1 — the dev
        cross-repo mirror is intentionally not absorbed."""
        from gald3r.systems.tier import TierSystem
        return TierSystem(self.config)

    @property
    def platform(self) -> "PlatformSystem":
        """Platform capability reporting over the generated matrix. Absorbs the read
        path of custom_scripts/check_platform_status.ps1."""
        from gald3r.systems.platform import PlatformSystem
        return PlatformSystem(self.config)

    @property
    def sync(self) -> "SyncSystem":
        """Canonical → platform-mirror parity (check/apply). Absorbs the live transform
        of custom_scripts/platform_parity_sync.ps1."""
        from gald3r.systems.sync import SyncSystem
        return SyncSystem(self.config)

    @property
    def validate(self) -> "ValidateSystem":
        """Deterministic validation gate over task/bug files: schema + status
        normalization + folder placement + index agreement (T520). Read-only unless
        run with fix=True; backs the `gald3r validate` command and the pre-commit hook."""
        from gald3r.systems.validate import ValidateSystem
        return ValidateSystem(self)

    @property
    def merge(self) -> "MergeSystem":
        """Cross-project item merge keyed on the stable uuid (T522 AC5): same-uuid skip,
        different-uuid + colliding display-id renumber-incoming. Pure planning over item
        collections; the caller persists + rewrites references."""
        from gald3r.merge import MergeSystem
        return MergeSystem(self.config)

    @property
    def release(self) -> ReleaseSystem:
        return ReleaseSystem(self.config)

    @property
    def plugins(self) -> "PluginSystem":
        """Plugin lifecycle ops (INSTALL/REMOVE/LIST/NEW/CHECK_COMPAT/UPDATE) over
        `.gald3r_sys/plugins/` — the manifest schema, registry config, and `installed.yaml`
        ledger live here (single source; T663). Additive install (D6 conflict-abort,
        plugin_source: provenance); never auto-runs lifecycle scripts (D7)."""
        from gald3r.systems.plugins import PluginSystem
        return PluginSystem(self.config)

    @property
    def upgrade(self) -> "UpgradeSystem":
        """Self-update: version-check against world_tree + safe `.gald3r/` migration
        (timestamped gitignored backup -> ADD/MERGE/DEPRECATE migration -> rollback on
        failure). Shared core for the agent (T473) and template-installed projects (T475)."""
        from gald3r.systems.upgrade import UpgradeSystem
        return UpgradeSystem(self.config)

    @property
    def prompts(self) -> PromptLibrary:
        """The judgment/prompt layer — package-shipped reasoning assets (persona, role
        briefs, review rubrics, playbooks). Serves prompt text; never executes it."""
        return PromptLibrary()

    @property
    def workspace(self) -> "WorkspaceSystem":
        """Cross-project coordination (WPAC / Workspace-Control). Controller-tier:
        ships dormant in lower tiers, so the facade refuses it there."""
        if not self.config.tier_at_least("controller"):
            raise PermissionError(
                f"workspace is controller-tier; this install is '{self.config.tier}'")
        from gald3r.systems.workspace import WorkspaceSystem
        return WorkspaceSystem(self.config)
