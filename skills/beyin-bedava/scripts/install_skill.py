#!/usr/bin/env python3
"""Install a project-local skill and verify files, Codex discovery and host activation."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
from pathlib import Path

NAME = "beyin-bedava"
VERSION = "3.0.0"
PROBE_PREFIX = "BB30"
SOURCE = Path(__file__).resolve().parents[1]
PROBE = Path("resources/activation-probe.txt")
HOSTS = {
    "codex": (".agents/skills", "$beyin-bedava"),
    "claude-code": (".claude/skills", "/beyin-bedava"),
    "antigravity": (".agents/skills", "/beyin-bedava"),
}
GENERATED = {"__pycache__", "node_modules", "dist", ".godot", ".build", ".dart_tool", "build",
             "Library", "Logs", "Temp", "UserSettings", ".gradle", ".swiftpm"}
ACTIVATE = ("Installation probe only. Follow the skill's activation probe instructions and return "
            "the marker as a single line.")
CONTROL = "This is a non-game control. Reply exactly CONTROL_OK and do not open any files."


def manifest(root):
    files = {}
    for directory, subdirectories, filenames in os.walk(root):
        parent = Path(directory)
        subdirectories[:] = [name for name in subdirectories
                           if name not in GENERATED and not (parent / name).is_symlink()]
        for name in filenames:
            path = parent / name
            relative = path.relative_to(root)
            if (relative != PROBE and path.is_file() and not path.is_symlink()
                    and path.suffix not in (".pyc", ".uid")
                    and name not in {".DS_Store", ".flutter-plugins-dependencies", ".metadata"}):
                files[relative] = path
    return files


def install(destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        if matching(destination):
            return
        raise ValueError(f"existing skill differs; pick a clean project or migrate it manually: {destination}")
    with tempfile.TemporaryDirectory(prefix=".beyin-install-", dir=destination.parent) as scratch:
        package = Path(scratch) / "skill"
        for relative, source in manifest(SOURCE).items():
            target = package / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        try:
            if destination.exists() or destination.is_symlink():
                raise FileExistsError(destination)
            package.rename(destination)
        except OSError:
            if not matching(destination):
                raise


def matching(destination):
    if destination.is_symlink():
        return False
    installed, source = manifest(destination), manifest(SOURCE)
    return source.keys() == installed.keys() and all(
        path.read_bytes() == installed[relative].read_bytes() for relative, path in source.items()
    )


async def codex_discovery(project, installed):
    messages = [
        {"id": 0, "method": "initialize", "params": {"clientInfo": {"name": NAME, "version": VERSION}}},
        {"method": "initialized"},
        {"id": 1, "method": "skills/list", "params": {"cwds": [str(project)], "forceReload": True}},
    ]
    process = await asyncio.create_subprocess_exec(
        "codex", "app-server", cwd=project, stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        async def request():
            for message in messages:
                process.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
                await process.stdin.drain()
                if message.get("id") is None:
                    continue
                while line := await process.stdout.readline():
                    event = json.loads(line)
                    if event.get("id") == message["id"]:
                        if "error" in event:
                            raise ValueError(f"Codex rejected {message['method']}")
                        break
                else:
                    raise ValueError(f"Codex did not return {message['method']}")
            return event["result"]["data"]

        entries = await asyncio.wait_for(request(), timeout=20)
        return any(skill.get("name") == NAME and skill.get("enabled") is True
                   and Path(skill["path"]).resolve() == (installed / "SKILL.md").resolve()
                   for entry in entries for skill in entry["skills"])
    finally:
        if process.returncode is None:
            process.kill()
        await process.communicate()


def proof(probe, host, response, control):
    token = probe.read_text(encoding="utf-8").strip()
    if not re.fullmatch(rf"{PROBE_PREFIX}-{re.escape(host)}-[a-f0-9]{{32}}", token):
        raise ValueError("prepare a new activation probe for this host")
    return response.strip() == token and control.strip() == "CONTROL_OK"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", choices=HOSTS)
    parser.add_argument("command", choices=("install", "check", "discover", "prepare", "verify"))
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--response", type=Path)
    parser.add_argument("--control", type=Path)
    args = parser.parse_args()
    root, prefix = HOSTS[args.host]
    project = args.project.resolve()
    destination = project / root / NAME
    result = {"host": args.host, "path": str(destination), "check": args.command}
    try:
        if not project.is_dir():
            raise ValueError("project must be an existing directory")
        if not destination.parent.resolve().is_relative_to(project):
            raise ValueError("skill directory must stay within the project")
        if args.command == "install":
            install(destination)
        if not matching(destination):
            raise ValueError("installed skill files are missing or differ from this release")
        if args.command == "discover":
            if args.host != "codex":
                raise ValueError("use prepare and verify with the selected host's native command")
            if not asyncio.run(codex_discovery(project, destination)):
                raise ValueError("Codex did not report the enabled project skill")
        if args.command == "prepare":
            with (destination / PROBE).open("x", encoding="utf-8") as handle:
                handle.write(f"{PROBE_PREFIX}-{args.host}-{secrets.token_hex(16)}\n")
            result.update(positive_prompt=f"{prefix} {ACTIVATE}", negative_prompt=CONTROL)
        if args.command == "verify":
            if args.response is None or args.control is None:
                raise ValueError("supply separate host outputs with --response and --control")
            if not proof(destination / PROBE, args.host, args.response.read_text(encoding="utf-8"),
                         args.control.read_text(encoding="utf-8")):
                raise ValueError("positive marker or negative control did not match")
            result["evidence"] = "operator_supplied_host_responses"
        result["status"] = "passed"
    except (OSError, ValueError, KeyError, asyncio.TimeoutError) as exc:
        result.update(status="failed", error=str(exc) or type(exc).__name__)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    sys.exit(main())
