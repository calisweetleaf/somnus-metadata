# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1af7c-0a38-7225-b7d7-bbcff55ed73f"
#   revision: 1
#   title: "Install the watcher under the user's service manager so it runs 24/7 (D20)"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a1af7c-0a38-7225-b7d7-bbcff55ed73f"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "install-the-watcher-under-the-user-s-service-manager-so-it-runs-24-7-d20"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1af7c-0a38-7225-b7d7-bbcff55ed73f"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Install the watcher under the user's service manager so it runs 24/7 (D20).

* Linux: a systemd **user** unit (``~/.config/systemd/user/somnus-watch.service``).
  ``loginctl enable-linger $USER`` keeps it running without an open session.
* macOS: a launchd agent (``~/Library/LaunchAgents/dev.somnus.watch.plist``).
* Windows: a logon scheduled task (``SomnusWatch``) running ``pythonw -m somnus watch``.

Every unit runs the same interpreter that ran the install, so a global
``~/.venvs/global`` install keeps using its own environment.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence
from xml.sax.saxutils import escape

UNIT_NAME = "somnus-watch.service"
LAUNCHD_LABEL = "dev.somnus.watch"
TASK_NAME = "SomnusWatch"

Runner = Callable[[Sequence[str]], tuple[int, str]]


def _run(argv: Sequence[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(list(argv), capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


@dataclass
class Plan:
    """What an install writes and runs."""

    platform: str
    path: Optional[Path]
    content: str
    commands: list[list[str]]
    hint: str = ""


def _quote(value: str) -> str:
    return f'"{value}"' if any(c in value for c in " \t\"\\") else value


def platform_name() -> str:
    """``linux``, ``darwin``, or ``windows``."""
    if os.name == "nt":
        return "windows"
    return "darwin" if sys.platform == "darwin" else "linux"


def python_for_service() -> str:
    """Interpreter for the service; on Windows prefer the windowless ``pythonw``."""
    exe = sys.executable or shutil.which("python3") or "python3"
    if os.name == "nt":
        candidate = Path(exe).with_name("pythonw.exe")
        if candidate.exists():
            return str(candidate)
    return exe


def install_plan(home: Path, platform: Optional[str] = None) -> Plan:
    """The unit file and commands for this platform."""
    platform = platform or platform_name()
    py = python_for_service()
    if platform == "linux":
        path = Path.home() / ".config" / "systemd" / "user" / UNIT_NAME
        content = (
            "[Unit]\n"
            "Description=Somnus metadata watcher (stamps and indexes registered roots)\n"
            "After=default.target\n\n"
            "[Service]\n"
            "Type=simple\n"
            f"ExecStart={_quote(py)} -m somnus watch\n"
            f"Environment=SOMNUS_HOME={home}\n"
            "Environment=PYTHONUNBUFFERED=1\n"
            "Restart=on-failure\n"
            "RestartSec=5\n"
            "Nice=10\n"
            "IOSchedulingClass=idle\n\n"
            "[Install]\n"
            "WantedBy=default.target\n"
        )
        cmds = [["systemctl", "--user", "daemon-reload"],
                ["systemctl", "--user", "enable", "--now", UNIT_NAME]]
        user = os.environ.get("USER", "$USER")
        return Plan(platform, path, content, cmds,
                    f"to keep it running while you are logged out: loginctl enable-linger {user}")
    if platform == "darwin":
        path = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        log = home / "watch.log"
        content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n<dict>\n'
            f"  <key>Label</key><string>{LAUNCHD_LABEL}</string>\n"
            "  <key>ProgramArguments</key>\n  <array>\n"
            f"    <string>{escape(py)}</string><string>-m</string><string>somnus</string><string>watch</string>\n"
            "  </array>\n"
            "  <key>EnvironmentVariables</key>\n  <dict>\n"
            f"    <key>SOMNUS_HOME</key><string>{escape(str(home))}</string>\n"
            "  </dict>\n"
            "  <key>RunAtLoad</key><true/>\n"
            "  <key>KeepAlive</key><true/>\n"
            "  <key>ProcessType</key><string>Background</string>\n"
            f"  <key>StandardOutPath</key><string>{escape(str(log))}</string>\n"
            f"  <key>StandardErrorPath</key><string>{escape(str(log))}</string>\n"
            "</dict>\n</plist>\n"
        )
        uid = str(os.getuid()) if hasattr(os, "getuid") else "501"
        cmds = [["launchctl", "bootout", f"gui/{uid}/{LAUNCHD_LABEL}"],
                ["launchctl", "bootstrap", f"gui/{uid}", str(path)]]
        return Plan(platform, path, content, cmds)
    task = f'"{py}" -m somnus watch'
    cmds = [["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/RL", "LIMITED", "/TN", TASK_NAME, "/TR", task],
            ["schtasks", "/Run", "/TN", TASK_NAME]]
    return Plan("windows", None, "", cmds, f"SOMNUS_HOME is read from the user environment ({home})")


def uninstall_plan(platform: Optional[str] = None) -> Plan:
    """Commands and the file an uninstall removes."""
    platform = platform or platform_name()
    if platform == "linux":
        return Plan(platform, Path.home() / ".config" / "systemd" / "user" / UNIT_NAME, "",
                    [["systemctl", "--user", "disable", "--now", UNIT_NAME], ["systemctl", "--user", "daemon-reload"]])
    if platform == "darwin":
        uid = str(os.getuid()) if hasattr(os, "getuid") else "501"
        return Plan(platform, Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist", "",
                    [["launchctl", "bootout", f"gui/{uid}/{LAUNCHD_LABEL}"]])
    return Plan("windows", None, "", [["schtasks", "/End", "/TN", TASK_NAME],
                                      ["schtasks", "/Delete", "/F", "/TN", TASK_NAME]])


def apply(plan: Plan, runner: Runner = _run, install: bool = True) -> list[str]:
    """Write/remove the unit and run its commands; returns human-readable result lines."""
    out: list[str] = []
    if install and plan.path is not None:
        plan.path.parent.mkdir(parents=True, exist_ok=True)
        plan.path.write_text(plan.content, encoding="utf-8")
        out.append(f"wrote {plan.path}")
    for i, argv in enumerate(plan.commands):
        code, text = runner(argv)
        # launchctl bootout before bootstrap fails harmlessly when nothing is loaded.
        tolerated = plan.platform == "darwin" and install and i == 0
        status = "ok" if code == 0 or tolerated else f"exit {code}"
        out.append(f"$ {' '.join(argv)}: {status}" + (f" ({text})" if text and code and not tolerated else ""))
    if not install and plan.path is not None and plan.path.exists():
        plan.path.unlink()
        out.append(f"removed {plan.path}")
    if install and plan.hint:
        out.append(plan.hint)
    return out
