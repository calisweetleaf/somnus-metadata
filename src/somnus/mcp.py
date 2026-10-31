"""Model Context Protocol server: every non-interactive ``somnus`` command as a stdio tool (D17).

Tools are generated from the CLI's argparse definitions, so the two surfaces cannot drift. Each
call runs the real CLI in a child process and returns its text output unchanged. JSON appears
only in the JSON-RPC framing that MCP requires; tool results stay text or TSV (D4).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Callable, Optional, Sequence

from somnus import __version__
from somnus.commands.brief import BRIEF
from somnus.output import EXIT_OK, EXIT_USAGE

PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
EXCLUDED = frozenset({"edit", "mcp"})
READ_ONLY = frozenset({"brief", "check", "ls", "q", "stale"})
SERVER_ONLY = frozenset({"actor", "no_color", "debug", "help"})
PATH_PARAMS = frozenset({"path", "paths", "roots", "root", "dir", "out"})
CALL_TIMEOUT = 600

ERR_PARSE, ERR_REQUEST, ERR_METHOD, ERR_PARAMS, ERR_INTERNAL = -32700, -32600, -32601, -32602, -32603

INSTRUCTIONS = BRIEF.rstrip("\n") + (
    "\n\n**MCP**\n\n"
    "Each tool runs the `somnus` command of the same name and returns its text output. A non-zero exit "
    "sets `isError` and ends the text with `[exit N]`. Relative paths resolve against the server's "
    "working directory, so pass absolute paths.\n"
)

Runner = Callable[[Sequence[str]], tuple[int, str]]


class ToolError(Exception):
    """Tool arguments that cannot become a command line; reported to the caller as a tool error."""


class ParamsError(Exception):
    """Malformed request parameters; reported as JSON-RPC error -32602."""


@dataclass(frozen=True)
class Param:
    """One CLI argument exposed as a tool property."""

    name: str
    flag: Optional[str]
    kind: str
    required: bool
    repeat: bool


@dataclass(frozen=True)
class Tool:
    """One CLI command exposed as an MCP tool."""

    name: str
    params: tuple[Param, ...]
    spec: dict


def _param(action: argparse.Action) -> Optional[tuple[Param, dict]]:
    if action.dest in SERVER_ONLY:
        return None
    flag = max(action.option_strings, key=len) if action.option_strings else None
    repeat = isinstance(action, argparse._AppendAction)
    if action.nargs == 0:
        kind = "boolean"
    elif repeat or action.nargs in ("+", "*"):
        kind = "array"
    elif action.type is int:
        kind = "integer"
    else:
        kind = "string"
    required = bool(action.required) if flag else action.nargs not in ("?", "*")
    prop: dict[str, Any] = {"type": kind}
    if kind == "array":
        prop["items"] = {"type": "string", **({"enum": list(action.choices)} if action.choices else {})}
        if action.nargs == "+":
            prop["minItems"] = 1
    elif action.choices:
        prop["enum"] = list(action.choices)
    description = action.help or (action.metavar if isinstance(action.metavar, str) else None)
    if description:
        prop["description"] = description
    if action.default not in (None, False, [], argparse.SUPPRESS):
        prop["default"] = action.default
    return Param(action.dest, flag, kind, required, repeat), prop


def build_tools() -> dict[str, Tool]:
    """MCP tools for every CLI command except the interactive ones."""
    from somnus.cli import build_parser

    parsers: dict[str, argparse.ArgumentParser] = {}
    build_parser(parsers)
    tools: dict[str, Tool] = {}
    for name, parser in parsers.items():
        if name in EXCLUDED:
            continue
        params: list[Param] = []
        properties: dict[str, dict] = {}
        # argparse has no public accessor for a parser's arguments; ``_actions`` is stable since 2.7.
        for action in parser._actions:
            built = _param(action)
            if built:
                params.append(built[0])
                properties[built[0].name] = built[1]
        spec = {
            "name": name,
            "description": f"{parser.description} (CLI: somnus {name})",
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": [p.name for p in params if p.required],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": name in READ_ONLY, "openWorldHint": False},
        }
        tools[name] = Tool(name, tuple(params), spec)
    return tools


def _text(param: Param, value: Any) -> str:
    if not isinstance(value, str):
        raise ToolError(f"{param.name} must be a string")
    if "\x00" in value:
        raise ToolError(f"{param.name} contains a NUL character")
    return value


def _tokens(param: Param, value: Any) -> list[str]:
    if param.kind == "boolean":
        if not isinstance(value, bool):
            raise ToolError(f"{param.name} must be true or false")
        return []
    if param.kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ToolError(f"{param.name} must be an integer")
        return [str(value)]
    if param.kind == "array":
        items = [value] if isinstance(value, str) else value
        if not isinstance(items, list):
            raise ToolError(f"{param.name} must be an array of strings")
        return [_text(param, item) for item in items]
    return [_text(param, value)]


def command_line(tool: Tool, arguments: Any) -> list[str]:
    """CLI arguments for one tool call.

    Option values use ``--flag=value`` and positionals follow ``--``, so values that begin with
    ``-`` are never read as options.
    """
    if not isinstance(arguments, dict):
        raise ToolError("arguments must be an object")
    unknown = sorted(set(arguments) - {p.name for p in tool.params})
    if unknown:
        raise ToolError(f"unknown argument(s): {', '.join(unknown)}")
    options: list[str] = []
    positionals: list[str] = []
    for param in tool.params:
        value = arguments.get(param.name)
        if value is None:
            if param.required:
                raise ToolError(f"missing required argument: {param.name}")
            continue
        tokens = _tokens(param, value)
        if param.flag is None:
            positionals.extend(tokens)
        elif param.kind == "boolean":
            if value:
                options.append(param.flag)
        else:
            options.extend(f"{param.flag}={token}" for token in tokens)
    return [tool.name, *options, *(["--", *positionals] if positionals else [])]


def run_cli(argv: Sequence[str], actor: Optional[str] = None) -> tuple[int, str]:
    """Run ``somnus`` in a child process; return its exit code and combined stdout/stderr text."""
    cmd = [sys.executable, "-m", "somnus.cli", "--no-color", *([f"--actor={actor}"] if actor else []), *argv]
    package_root = str(Path(__file__).resolve().parent.parent)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", NO_COLOR="1")
    env["PYTHONPATH"] = os.pathsep.join(p for p in (package_root, os.environ.get("PYTHONPATH")) if p)
    try:
        # CREATE_NO_WINDOW: a GUI-launched server has no console, and each child would open one.
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, env=env,
                              timeout=CALL_TIMEOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return EXIT_USAGE, f"somnus {argv[0]} timed out after {CALL_TIMEOUT} seconds"
    except OSError as exc:
        return EXIT_USAGE, f"could not start somnus: {exc}"
    parts = (stream.decode("utf-8", "replace").replace("\r\n", "\n") for stream in (proc.stdout, proc.stderr))
    return proc.returncode, "\n".join(p.rstrip("\n") for p in parts if p.strip())


def _relative_paths(arguments: dict) -> list[str]:
    """Relative path arguments of a call, for the hint on a failed call."""
    out: list[str] = []
    for name in PATH_PARAMS & set(arguments):
        value = arguments[name]
        for item in [value] if isinstance(value, str) else value if isinstance(value, list) else []:
            if isinstance(item, str) and item and not Path(item).is_absolute():
                out.append(item)
    return sorted(out)


def _error(mid: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


class Server:
    """Stateless request handler; one instance serves one stdio session."""

    def __init__(self, actor: Optional[str] = None, runner: Optional[Runner] = None) -> None:
        self.tools = build_tools()
        self.runner: Runner = runner or (lambda argv: run_cli(argv, actor))

    def handle(self, message: Any) -> Optional[dict]:
        """Response for one JSON-RPC message, or None for notifications and stray responses."""
        if not isinstance(message, dict):
            return _error(None, ERR_REQUEST, "invalid request")
        if "method" not in message and ("result" in message or "error" in message):
            return None
        mid = message.get("id")
        method = message.get("method")
        if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
            return _error(mid, ERR_REQUEST, "invalid request")
        if "id" not in message:
            return None
        params = message.get("params") or {}
        try:
            if not isinstance(params, dict):
                raise ParamsError("params must be an object")
            if method == "initialize":
                result = self.initialize(params)
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": [t.spec for t in self.tools.values()]}
            elif method == "tools/call":
                result = self.call(params)
            else:
                return _error(mid, ERR_METHOD, f"method not found: {method}")
        except ParamsError as exc:
            return _error(mid, ERR_PARAMS, str(exc))
        except Exception as exc:  # noqa: BLE001 - one bad request must not end the session
            sys.stderr.write(f"somnus mcp: internal error in {method}: {type(exc).__name__}: {exc}\n")
            return _error(mid, ERR_INTERNAL, f"internal error: {type(exc).__name__}")
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def initialize(self, params: dict) -> dict:
        """Negotiate the protocol version and describe the server."""
        requested = params.get("protocolVersion")
        return {
            "protocolVersion": requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "somnus", "version": __version__},
            "instructions": INSTRUCTIONS,
        }

    def call(self, params: dict) -> dict:
        """Run one tool; argument problems and non-zero exits come back as tool errors."""
        name = params.get("name")
        tool = self.tools.get(name) if isinstance(name, str) else None
        if tool is None:
            raise ParamsError(f"unknown tool: {params.get('name')!r}")
        try:
            argv = command_line(tool, params.get("arguments") or {})
        except ToolError as exc:
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        code, text = self.runner(argv)
        if code != EXIT_OK:
            relative = _relative_paths(params.get("arguments") or {})
            if relative:
                text += (f"\nnote: relative path(s) {', '.join(relative)} resolve from the server directory"
                         f" {os.getcwd()}; pass absolute paths")
            text = f"{text}\n[exit {code}]" if text else f"[exit {code}]"
        return {"content": [{"type": "text", "text": text or "(no output)"}], "isError": code != EXIT_OK}


def _reply(server: Server, message: Any) -> Any:
    if not isinstance(message, list):
        return server.handle(message)
    if not message:
        return _error(None, ERR_REQUEST, "empty batch")
    replies = [r for r in map(server.handle, message) if r is not None]
    return replies or None


def serve(actor: Optional[str] = None, stdin: Optional[BinaryIO] = None, stdout: Optional[BinaryIO] = None,
          runner: Optional[Runner] = None) -> int:
    """Read newline-delimited JSON-RPC from stdin until EOF, answering on stdout."""
    server = Server(actor, runner)
    source = stdin or sys.stdin.buffer
    sink = stdout or sys.stdout.buffer
    while True:
        raw = source.readline()
        if not raw:
            return EXIT_OK
        line = raw.strip()
        if not line:
            continue
        try:
            message = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            reply: Any = _error(None, ERR_PARSE, "parse error")
        else:
            reply = _reply(server, message)
        if reply is not None:
            sink.write(json.dumps(reply, separators=(",", ":")).encode("ascii") + b"\n")
            sink.flush()
