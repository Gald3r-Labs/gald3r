"""
Health Check System for Agent SDK Integration

Validates agent environment, SDK availability, and system resources
to prevent failures before they occur.
"""

import logging
import sys
import os
import importlib.util
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import json


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthCheck:
    """Base health check class"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = HealthStatus.UNKNOWN
        self.message = ""
        self.details = {}

    def check(self) -> HealthStatus:
        """Run health check - override in subclasses"""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }


class SDKAvailabilityCheck(HealthCheck):
    """Check if Anthropic SDK is installed and importable"""

    def __init__(self):
        super().__init__(
            name="sdk_availability",
            description="Anthropic SDK installation and import"
        )

    def check(self) -> HealthStatus:
        """Check SDK availability"""
        try:
            # Check if anthropic module exists
            spec = importlib.util.find_spec("anthropic")

            if spec is None:
                self.status = HealthStatus.CRITICAL
                self.message = "Anthropic SDK not installed"
                self.details = {
                    "installed": False,
                    "install_command": "pip install anthropic>=0.40.0"
                }
                return self.status

            # Try to import
            import anthropic

            # Check version
            version = getattr(anthropic, "__version__", "unknown")
            self.status = HealthStatus.HEALTHY
            self.message = "SDK available"
            self.details = {
                "installed": True,
                "version": version,
                "location": spec.origin
            }

        except ImportError as e:
            self.status = HealthStatus.CRITICAL
            self.message = f"SDK import failed: {e}"
            self.details = {"installed": True, "importable": False, "error": str(e)}

        except Exception as e:
            self.status = HealthStatus.WARNING
            self.message = f"SDK check failed: {e}"
            self.details = {"error": str(e)}

        return self.status


class APIKeyCheck(HealthCheck):
    """Check if Anthropic API key is configured"""

    def __init__(self):
        super().__init__(
            name="api_key",
            description="Anthropic API key configuration"
        )

    def check(self) -> HealthStatus:
        """Check API key"""
        # Check environment variable
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            self.status = HealthStatus.CRITICAL
            self.message = "ANTHROPIC_API_KEY not set"
            self.details = {
                "configured": False,
                "help": "Set ANTHROPIC_API_KEY environment variable"
            }
            return self.status

        # Basic validation (should start with sk-)
        if not api_key.startswith("sk-"):
            self.status = HealthStatus.WARNING
            self.message = "API key format may be invalid"
            self.details = {
                "configured": True,
                "format_valid": False,
                "help": "API key should start with 'sk-'"
            }
            return self.status

        self.status = HealthStatus.HEALTHY
        self.message = "API key configured"
        self.details = {
            "configured": True,
            "format_valid": True,
            "length": len(api_key)
        }

        return self.status


class AgentFilesCheck(HealthCheck):
    """Check if agent files exist and are valid"""

    def __init__(self, agent_dir: Path = None):
        super().__init__(
            name="agent_files",
            description="Agent file existence and validity"
        )
        self.agent_dir = agent_dir or Path(".claude/agents")

    def check(self) -> HealthStatus:
        """Check agent files"""
        issues = []
        agents_found = []

        # Check SDK agents
        sdk_dir = self.agent_dir / "sdk" / "agents"
        if sdk_dir.exists():
            for agent_file in sdk_dir.glob("*.py"):
                if agent_file.name != "__init__.py":
                    agents_found.append(f"SDK: {agent_file.stem}")

        # Check prompt-based agents
        prompt_dirs = [
            self.agent_dir / "prompt-based",
            self.agent_dir  # Legacy location
        ]

        for prompt_dir in prompt_dirs:
            if prompt_dir.exists():
                for agent_file in prompt_dir.glob("*.md"):
                    agents_found.append(f"Prompt: {agent_file.stem}")

        if not agents_found:
            self.status = HealthStatus.CRITICAL
            self.message = "No agents found"
            issues.append("No agent files exist")
        elif len(agents_found) < 5:
            self.status = HealthStatus.WARNING
            self.message = f"Only {len(agents_found)} agents found"
            issues.append("Expected at least 5 agents")
        else:
            self.status = HealthStatus.HEALTHY
            self.message = f"{len(agents_found)} agents available"

        self.details = {
            "agents_found": len(agents_found),
            "agents": agents_found[:10],  # First 10
            "issues": issues
        }

        return self.status


class ContextStorageCheck(HealthCheck):
    """Check context storage directories and permissions"""

    def __init__(self, context_dir: Path = None):
        super().__init__(
            name="context_storage",
            description="Context storage directories and permissions"
        )
        self.context_dir = context_dir or Path(".claude/agent_context")

    def check(self) -> HealthStatus:
        """Check context storage"""
        issues = []

        # Check if directory exists
        if not self.context_dir.exists():
            try:
                self.context_dir.mkdir(parents=True, exist_ok=True)
                self.status = HealthStatus.HEALTHY
                self.message = "Context directory created"
            except Exception as e:
                self.status = HealthStatus.CRITICAL
                self.message = "Cannot create context directory"
                issues.append(f"Creation failed: {e}")
                self.details = {"issues": issues}
                return self.status

        # Check write permissions
        test_file = self.context_dir / ".health_check_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            can_write = True
        except Exception as e:
            can_write = False
            issues.append(f"No write permission: {e}")

        # Check subdirectories
        subdirs = ["sdk", "json", "active", "archived"]
        for subdir in subdirs:
            subdir_path = self.context_dir / subdir
            if not subdir_path.exists():
                try:
                    subdir_path.mkdir(exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create {subdir}: {e}")

        if not can_write:
            self.status = HealthStatus.CRITICAL
            self.message = "No write permission"
        elif issues:
            self.status = HealthStatus.WARNING
            self.message = "Some subdirectories missing"
        else:
            self.status = HealthStatus.HEALTHY
            self.message = "Context storage ready"

        self.details = {
            "directory": str(self.context_dir),
            "writable": can_write,
            "subdirs": subdirs,
            "issues": issues
        }

        return self.status


class ResourceCheck(HealthCheck):
    """Check system resources (memory, disk)"""

    def __init__(self,
                 memory_warning_threshold: int = 80,
                 memory_critical_threshold: int = 95,
                 disk_warning_threshold: int = 85,
                 disk_critical_threshold: int = 95):
        super().__init__(
            name="system_resources",
            description="System memory and disk space"
        )
        self.memory_warning = memory_warning_threshold
        self.memory_critical = memory_critical_threshold
        self.disk_warning = disk_warning_threshold
        self.disk_critical = disk_critical_threshold

    def check(self) -> HealthStatus:
        """Check system resources"""
        issues = []

        # Check memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        if memory_percent >= self.memory_critical:
            issues.append(f"Memory critical: {memory_percent}%")
            status = HealthStatus.CRITICAL
        elif memory_percent >= self.memory_warning:
            issues.append(f"Memory high: {memory_percent}%")
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY

        # Check disk
        disk = psutil.disk_usage('.')
        disk_percent = disk.percent

        if disk_percent >= self.disk_critical:
            issues.append(f"Disk critical: {disk_percent}%")
            status = HealthStatus.CRITICAL
        elif disk_percent >= self.disk_warning:
            issues.append(f"Disk high: {disk_percent}%")
            if status != HealthStatus.CRITICAL:
                status = HealthStatus.WARNING

        self.status = status
        self.message = "Resources OK" if not issues else "; ".join(issues)
        self.details = {
            "memory_percent": memory_percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk_percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "issues": issues
        }

        return self.status


class NetworkCheck(HealthCheck):
    """Check network connectivity to Anthropic API"""

    def __init__(self):
        super().__init__(
            name="network_connectivity",
            description="Network access to Anthropic API"
        )

    def check(self) -> HealthStatus:
        """Check network connectivity"""
        try:
            import socket
            import urllib.request

            # Check DNS resolution
            socket.gethostbyname("api.anthropic.com")

            # Try to connect (don't make actual API call)
            req = urllib.request.Request(
                "https://api.anthropic.com",
                headers={"User-Agent": "Health Check"}
            )
            urllib.request.urlopen(req, timeout=5)

            self.status = HealthStatus.HEALTHY
            self.message = "Network connectivity OK"
            self.details = {"reachable": True}

        except socket.gaierror:
            self.status = HealthStatus.CRITICAL
            self.message = "DNS resolution failed"
            self.details = {"reachable": False, "error": "DNS failure"}

        except urllib.error.URLError as e:
            self.status = HealthStatus.WARNING
            self.message = "Network connection issues"
            self.details = {"reachable": False, "error": str(e)}

        except Exception as e:
            self.status = HealthStatus.WARNING
            self.message = f"Network check failed: {e}"
            self.details = {"error": str(e)}

        return self.status


class HealthMonitor:
    """
    Comprehensive health monitoring system

    Runs all health checks and provides overall system status
    """

    def __init__(self, log_dir: Path = None):
        """
        Initialize health monitor

        Args:
            log_dir: Directory for health logs
        """
        self.log_dir = log_dir or Path(".claude/agents/sdk/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = self._setup_logger()

        # Initialize checks
        self.checks: List[HealthCheck] = [
            SDKAvailabilityCheck(),
            APIKeyCheck(),
            AgentFilesCheck(),
            ContextStorageCheck(),
            ResourceCheck(),
            NetworkCheck()
        ]

    def _setup_logger(self) -> logging.Logger:
        """Setup health logging"""
        logger = logging.getLogger("HealthMonitor")
        logger.setLevel(logging.INFO)

        fh = logging.FileHandler(self.log_dir / "health.log")
        fh.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)

        logger.addHandler(fh)
        return logger

    def run_checks(self) -> Dict[str, Any]:
        """
        Run all health checks

        Returns:
            Health report
        """
        results = []
        overall_status = HealthStatus.HEALTHY

        for check in self.checks:
            try:
                status = check.check()
                results.append(check.to_dict())

                # Determine overall status (worst status wins)
                if status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                elif status == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.WARNING

                self.logger.info(f"{check.name}: {status.value} - {check.message}")

            except Exception as e:
                self.logger.error(f"Check failed: {check.name}: {e}")
                results.append({
                    "name": check.name,
                    "status": HealthStatus.CRITICAL.value,
                    "message": f"Check failed: {e}",
                    "error": str(e)
                })
                overall_status = HealthStatus.CRITICAL

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "checks": results,
            "summary": self._generate_summary(results, overall_status)
        }

        # Write to file
        self._write_report(report)

        return report

    def _generate_summary(self,
                         results: List[Dict],
                         overall_status: HealthStatus) -> Dict[str, Any]:
        """Generate health summary"""
        status_counts = {
            "healthy": 0,
            "warning": 0,
            "critical": 0,
            "unknown": 0
        }

        for result in results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_checks": len(results),
            "status_counts": status_counts,
            "overall": overall_status.value,
            "ready_for_sdk": overall_status == HealthStatus.HEALTHY,
            "ready_for_prompt_based": status_counts["critical"] < len(results)
        }

    def _write_report(self, report: Dict[str, Any]):
        """Write health report to file"""
        report_file = self.log_dir / "latest_health.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Also append to history
        history_file = self.log_dir / "health_history.jsonl"
        with open(history_file, 'a') as f:
            f.write(json.dumps(report) + '\n')

    def get_agent_readiness(self) -> Tuple[bool, List[str]]:
        """
        Check if system is ready for agent execution

        Returns:
            (ready, issues) tuple
        """
        report = self.run_checks()
        issues = []

        for check in report["checks"]:
            if check["status"] in ["critical", "warning"]:
                issues.append(f"{check['name']}: {check['message']}")

        ready = report["overall_status"] in ["healthy", "warning"]

        return ready, issues

    def validate_agent(self, agent_name: str) -> Tuple[bool, str]:
        """
        Validate specific agent availability

        Args:
            agent_name: Agent to validate

        Returns:
            (valid, message) tuple
        """
        # Check SDK agent
        sdk_agent = Path(f".claude/agents/sdk/agents/{agent_name}.py")
        if sdk_agent.exists():
            return True, f"SDK agent available: {agent_name}"

        # Check prompt-based agent
        prompt_agent = Path(f".claude/agents/prompt-based/{agent_name}.md")
        if prompt_agent.exists():
            return True, f"Prompt-based agent available: {agent_name}"

        # Check legacy location
        legacy_agent = Path(f".claude/agents/{agent_name}.md")
        if legacy_agent.exists():
            return True, f"Legacy agent available: {agent_name}"

        return False, f"Agent not found: {agent_name}"

    def print_report(self, report: Dict[str, Any] = None):
        """Print health report to console"""
        if report is None:
            report = self.run_checks()

        print("\n" + "="*60)
        print("AGENT SDK HEALTH CHECK REPORT")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print()

        print("Individual Checks:")
        print("-"*60)

        for check in report["checks"]:
            status_symbol = {
                "healthy": "✓",
                "warning": "⚠",
                "critical": "✗",
                "unknown": "?"
            }.get(check["status"], "?")

            print(f"{status_symbol} {check['name']}: {check['message']}")

        print()
        print("Summary:")
        print("-"*60)
        summary = report["summary"]
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Healthy: {summary['status_counts']['healthy']}")
        print(f"Warning: {summary['status_counts']['warning']}")
        print(f"Critical: {summary['status_counts']['critical']}")
        print()
        print(f"Ready for SDK: {summary['ready_for_sdk']}")
        print(f"Ready for Prompt-based: {summary['ready_for_prompt_based']}")
        print("="*60)


# CLI interface
if __name__ == "__main__":
    monitor = HealthMonitor()

    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        # Validate specific agent
        agent_name = sys.argv[2] if len(sys.argv) > 2 else "backend-developer"
        valid, message = monitor.validate_agent(agent_name)
        print(message)
        sys.exit(0 if valid else 1)

    elif len(sys.argv) > 1 and sys.argv[1] == "readiness":
        # Check readiness
        ready, issues = monitor.get_agent_readiness()
        if ready:
            print("System ready for agent execution")
            sys.exit(0)
        else:
            print("System NOT ready:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)

    else:
        # Full health check
        report = monitor.run_checks()
        monitor.print_report(report)
