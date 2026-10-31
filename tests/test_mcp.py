"""MCP server: protocol handling, argparse-derived tools, argv construction, and a live stdio session."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import somnus
from somnus import mcp
from somnus.cli import build_parser


def request(mid, method, params=None) -> dict:
    msg = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


class FakeRunner:
    def __init__(self, code: int = 0, text: str = "ok") -> None:
        self.code, self.text, self.calls = code, text, []

    def __call__(self, argv):
        self.calls.append(list(argv))
        return self.code, self.text


class TestProtocol(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = FakeRunner()
        self.server = mcp.Server(runner=self.runner)

    def test_initialize_negotiates_version(self) -> None:
        res = self.server.handle(request(1, "initialize", {"protocolVersion": "2025-06-18"}))["result"]
        self.assertEqual(res["protocolVersion"], "2025-06-18")
        self.assertEqual(res["serverInfo"]["name"], "somnus")
        self.assertIn("tools", res["capabilities"])
        self.assertIn("Rules for agents", res["instructions"])
        res = self.server.handle(request(2, "initialize", {"protocolVersion": "1999-01-01"}))["result"]
        self.assertEqual(res["protocolVersion"], mcp.PROTOCOL_VERSIONS[0])

    def test_notifications_and_responses_get_no_reply(self) -> None:
        self.assertIsNone(self.server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertIsNone(self.server.handle({"jsonrpc": "2.0", "id": 9, "result": {}}))

    def test_errors(self) -> None:
        self.assertEqual(self.server.handle(request(1, "nope"))["error"]["code"], mcp.ERR_METHOD)
        self.assertEqual(self.server.handle(request(2, "tools/call", ["x"]))["error"]["code"], mcp.ERR_PARAMS)
        self.assertEqual(self.server.handle(request(3, "tools/call", {"name": "edit"}))["error"]["code"],
                         mcp.ERR_PARAMS)
        self.assertEqual(self.server.handle({"id": 4, "method": "ping"})["error"]["code"], mcp.ERR_REQUEST)
        self.assertEqual(self.server.handle("x")["error"]["code"], mcp.ERR_REQUEST)
        self.assertEqual(self.server.handle(request(5, "ping")), {"jsonrpc": "2.0", "id": 5, "result": {}})

    def test_call_maps_exit_codes(self) -> None:
        res = self.server.handle(request(1, "tools/call", {"name": "brief"}))["result"]
        self.assertEqual(res, {"content": [{"type": "text", "text": "ok"}], "isError": False})
        self.assertEqual(self.runner.calls, [["brief"]])
        self.runner.code, self.runner.text = 1, "a.md:1:1: error E_SCHEMA x: bad"
        res = self.server.handle(request(2, "tools/call", {"name": "check", "arguments": {"paths": ["a.md"]}}))
        self.assertTrue(res["result"]["isError"])
        text = res["result"]["content"][0]["text"]
        self.assertTrue(text.startswith("a.md:1:1: error E_SCHEMA x: bad\nnote: relative path(s) a.md resolve from"))
        self.assertIn(os.getcwd(), text)
        self.assertTrue(text.endswith("; pass absolute paths\n[exit 1]"))
        absolute = str(Path(os.getcwd(), "a.md"))
        res = self.server.handle(request(4, "tools/call", {"name": "check", "arguments": {"paths": [absolute]}}))
        self.assertTrue(res["result"]["content"][0]["text"].endswith("bad\n[exit 1]"))
        self.runner.code, self.runner.text = 0, ""
        res = self.server.handle(request(3, "tools/call", {"name": "brief"}))["result"]
        self.assertEqual(res["content"][0]["text"], "(no output)")

    def test_bad_arguments_are_tool_errors(self) -> None:
        res = self.server.handle(request(1, "tools/call", {"name": "check", "arguments": {"wat": 1}}))["result"]
        self.assertTrue(res["isError"])
        self.assertIn("unknown argument(s): wat", res["content"][0]["text"])
        self.assertEqual(self.runner.calls, [])

    def test_serve_reads_lines_and_batches(self) -> None:
        lines = [json.dumps(request(1, "ping")), "", "{broken",
                 json.dumps([request(2, "ping"), {"jsonrpc": "2.0", "method": "notifications/initialized"}]),
                 json.dumps([])]
        sink = io.BytesIO()
        code = mcp.serve(stdin=io.BytesIO(("\n".join(lines) + "\n").encode()), stdout=sink, runner=self.runner)
        self.assertEqual(code, 0)
        replies = [json.loads(line) for line in sink.getvalue().decode("ascii").splitlines()]
        self.assertEqual(replies[0]["result"], {})
        self.assertEqual(replies[1]["error"]["code"], mcp.ERR_PARSE)
        self.assertEqual([r["id"] for r in replies[2]], [2])
        self.assertEqual(replies[3]["error"]["code"], mcp.ERR_REQUEST)


class TestRunnerFailures(unittest.TestCase):
    def test_internal_error_is_contained_and_the_session_survives(self) -> None:
        def runner(argv):
            raise RuntimeError("disk exploded")

        server = mcp.Server(runner=runner)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            reply = server.handle(request(1, "tools/call", {"name": "brief"}))
        self.assertEqual(reply["error"]["code"], mcp.ERR_INTERNAL)
        self.assertEqual(reply["error"]["message"], "internal error: RuntimeError")
        self.assertIn("disk exploded", err.getvalue())
        self.assertEqual(server.handle(request(2, "ping"))["result"], {})


class TestRunCli(unittest.TestCase):
    def completed(self, stdout: bytes, stderr: bytes, code: int = 0) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess([], code, stdout, stderr)

    def test_runs_the_cli_in_a_child_process(self) -> None:
        home = tempfile.mkdtemp()
        try:
            with mock.patch.dict(os.environ, {"SOMNUS_HOME": home}):
                code, text = mcp.run_cli(["brief"])
        finally:
            shutil.rmtree(home, ignore_errors=True)
        self.assertEqual(code, 0)
        self.assertIn("somnus status", text)

    def test_actor_and_package_path_reach_the_child(self) -> None:
        with mock.patch.object(mcp.subprocess, "run", return_value=self.completed(b"", b"")) as run:
            mcp.run_cli(["brief"], actor="bob")
        cmd = run.call_args.args[0]
        self.assertIn("--actor=bob", cmd)
        self.assertEqual(cmd[-1], "brief")
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(run.call_args.kwargs["timeout"], mcp.CALL_TIMEOUT)
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertIn(str(Path(mcp.__file__).resolve().parent.parent), env["PYTHONPATH"].split(os.pathsep))

    def test_streams_are_merged_normalized_and_decoded_leniently(self) -> None:
        proc = self.completed(b"out line\r\n", b"bad \xff byte\n", code=1)
        with mock.patch.object(mcp.subprocess, "run", return_value=proc):
            code, text = mcp.run_cli(["check"])
        self.assertEqual(code, 1)
        self.assertEqual(text, "out line\nbad \ufffd byte")

    def test_timeout_is_a_usage_failure_naming_the_command(self) -> None:
        boom = subprocess.TimeoutExpired(["somnus"], mcp.CALL_TIMEOUT)
        with mock.patch.object(mcp.subprocess, "run", side_effect=boom):
            code, text = mcp.run_cli(["index"])
        self.assertEqual(code, 2)
        self.assertEqual(text, f"somnus index timed out after {mcp.CALL_TIMEOUT} seconds")

    def test_unstartable_child_is_a_usage_failure(self) -> None:
        with mock.patch.object(mcp.subprocess, "run", side_effect=FileNotFoundError(2, "No such file")):
            code, text = mcp.run_cli(["index"])
        self.assertEqual(code, 2)
        self.assertTrue(text.startswith("could not start somnus: "))


class TestTools(unittest.TestCase):
    def setUp(self) -> None:
        self.tools = mcp.build_tools()

    def parse(self, name: str, arguments: dict):
        return build_parser().parse_args(mcp.command_line(self.tools[name], arguments))

    def test_every_noninteractive_command_is_a_tool(self) -> None:
        parsers: dict = {}
        build_parser(parsers)
        self.assertEqual(set(self.tools), set(parsers) - {"edit", "mcp"})
        for tool in self.tools.values():
            schema = tool.spec["inputSchema"]
            self.assertFalse(schema["additionalProperties"])
            self.assertFalse({"actor", "debug", "no_color", "help"} & set(schema["properties"]))
            self.assertEqual(tool.spec["annotations"]["readOnlyHint"], tool.name in mcp.READ_ONLY)

    def test_schemas_follow_argparse(self) -> None:
        new = self.tools["new"].spec["inputSchema"]
        self.assertEqual(new["required"], ["type", "title"])
        self.assertIn("specification", new["properties"]["type"]["enum"])
        self.assertEqual(new["properties"]["dir"]["default"], ".")
        status = self.tools["status"].spec["inputSchema"]["properties"]
        self.assertEqual(status["replacement"]["type"], "array")
        self.assertEqual(self.tools["q"].spec["inputSchema"]["properties"]["limit"]["type"], "integer")
        self.assertEqual(self.tools["set"].spec["inputSchema"]["properties"]["assignments"]["minItems"], 1)

    def test_command_lines_round_trip_through_argparse(self) -> None:
        args = self.parse("set", {"path": "-odd.md", "assignments": ["title=-x", "summary=y"], "reason": "-r"})
        self.assertEqual((args.command, args.path, args.assignments, args.reason),
                         ("set", "-odd.md", ["title=-x", "summary=y"], "-r"))
        args = self.parse("status", {"path": "a.md", "new_status": "superseded",
                                     "replacement": ["urn:somnus:artifact:1", "urn:somnus:artifact:2"]})
        self.assertEqual(args.replacement, ["urn:somnus:artifact:1", "urn:somnus:artifact:2"])
        args = self.parse("q", {"sql": "-- comment\nSELECT 1", "limit": 5, "tsv": True})
        self.assertEqual((args.sql, args.limit, args.tsv), ("-- comment\nSELECT 1", 5, True))
        args = self.parse("check", {"paths": "one.md", "all": False, "level": "semantic"})
        self.assertEqual((args.paths, args.all, args.level), (["one.md"], False, "semantic"))
        self.assertEqual(mcp.command_line(self.tools["stale"], {}), ["stale"])

    def test_argument_validation(self) -> None:
        line = mcp.command_line
        for name, arguments in (("new", {"type": "plan"}), ("q", {"limit": "5"}), ("q", {"limit": True}),
                                ("check", {"all": "yes"}), ("check", {"paths": [1]}), ("new", "x"),
                                ("check", {"paths": {"a": "b"}}),
                                ("bump", {"path": "a\x00b"})):
            with self.assertRaises(mcp.ToolError, msg=f"{name} {arguments!r}"):
                line(self.tools[name], arguments)


class TestLiveSession(unittest.TestCase):
    """Drives ``somnus mcp`` as a real child process, the way an MCP client does."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        env = dict(os.environ, SOMNUS_HOME=str(self.tmp / "home"),
                   PYTHONPATH=str(Path(somnus.__file__).resolve().parents[1]))
        self.proc = subprocess.Popen([sys.executable, "-m", "somnus.cli", "--actor", "mcp-test", "mcp"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     cwd=self.tmp, env=env)
        self.next_id = 0

    def tearDown(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(10)
        for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            stream.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rpc(self, method: str, params=None) -> dict:
        self.next_id += 1
        self.proc.stdin.write((json.dumps(request(self.next_id, method, params)) + "\n").encode())
        self.proc.stdin.flush()
        reply = json.loads(self.proc.stdout.readline())
        self.assertEqual(reply["id"], self.next_id)
        return reply

    def call(self, name: str, **arguments) -> dict:
        return self.rpc("tools/call", {"name": name, "arguments": arguments})["result"]

    def test_session(self) -> None:
        self.assertEqual(self.rpc("initialize", {"protocolVersion": "2025-06-18"})["result"]["protocolVersion"],
                         "2025-06-18")
        names = {t["name"] for t in self.rpc("tools/list")["result"]["tools"]}
        self.assertIn("set", names)
        self.assertFalse(self.call("init", root=[str(self.tmp)])["isError"])
        created = self.call("new", type="plan", title="Live Plan", dir=str(self.tmp))
        self.assertFalse(created["isError"], created)
        path = created["content"][0]["text"].splitlines()[0].strip()
        result = self.call("set", path=path, assignments=["title=Live Plan \u00e9", "classification.tags=x"])
        self.assertFalse(result["isError"], result)
        self.assertIn("revision 2", result["content"][0]["text"])
        self.assertIn("title: \"Live Plan \u00e9\"", Path(path).read_text(encoding="utf-8"))
        bad = self.call("check", paths=[str(self.tmp / "missing.md")])
        self.assertTrue(bad["isError"])
        events = self.call("q", sql="SELECT actor, action FROM events WHERE action = 'set'", tsv=True)
        self.assertEqual(events["content"][0]["text"].splitlines(), ["actor\taction", "mcp-test\tset"])
        self.proc.stdin.close()
        self.assertEqual(self.proc.wait(10), 0)


if __name__ == "__main__":
    unittest.main()
