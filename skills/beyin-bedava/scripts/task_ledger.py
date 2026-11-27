#!/usr/bin/env python3
"""Persistent task DAG, recovery checkpoints and single-writer file ownership."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

OWNERS = {"beyin-bedava", "tasarim-vergisi"}


def file_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or str(path) != value or value == ".":
        raise ValueError(f"expected a canonical repository-relative file: {value}")
    return value


class Ledger:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS plan (goal TEXT NOT NULL, baseline TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, acceptance TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL, token TEXT, lease REAL,
                checkpoint TEXT, evidence TEXT, problem TEXT
            );
            CREATE TABLE IF NOT EXISTS dependencies (
                task TEXT REFERENCES tasks, prerequisite TEXT REFERENCES tasks,
                PRIMARY KEY(task, prerequisite)
            );
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY, task TEXT NOT NULL REFERENCES tasks
            );
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY, task TEXT NOT NULL REFERENCES tasks,
                action TEXT NOT NULL, detail TEXT NOT NULL, at REAL NOT NULL
            );
        """)

    @contextmanager
    def transaction(self):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            yield

    def init(self, plan):
        if (not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list)
                or not plan["tasks"]):
            raise ValueError("a plan object with a nonempty tasks array is required")
        if not all(isinstance(plan.get(key), str) and plan[key].strip() for key in ("goal", "baseline")):
            raise ValueError("goal and baseline revision are required")
        tasks = {}
        for task in plan["tasks"]:
            if not isinstance(task, dict) or not isinstance(task.get("id"), str) or not task["id"].strip():
                raise ValueError("each task requires a nonempty string ID")
            task_id = task["id"]
            if task_id in tasks:
                raise ValueError(f"duplicate task ID: {task_id}")
            for field in ("depends", "files"):
                entries = task.get(field, [])
                if (not isinstance(entries, list) or not all(isinstance(item, str) and item.strip() for item in entries)
                        or len(set(entries)) != len(entries)):
                    raise ValueError(f"{task_id}: expected unique strings for {field}")
            tasks[task_id] = task
        ready = set()
        while ready != tasks.keys():
            next_ready = {key for key, task in tasks.items() if set(task.get("depends", [])) <= ready}
            if ready == next_ready:
                raise ValueError("cyclic or unknown dependencies")
            ready = next_ready
        with self.transaction():
            if self.db.execute("SELECT 1 FROM plan").fetchone():
                raise ValueError("ledger already initialized")
            self.db.execute("INSERT INTO plan VALUES (?, ?)", (plan["goal"], plan["baseline"]))
            for task_id, task in tasks.items():
                attempts = task.get("max_attempts", 3)
                if (task.get("owner") not in OWNERS or not isinstance(task.get("acceptance"), str)
                        or not task["acceptance"].strip() or type(attempts) is not int or not 1 <= attempts <= 1000):
                    raise ValueError(f"invalid owner, acceptance or attempt budget for {task_id}")
                self.db.execute("INSERT INTO tasks (id, owner, acceptance, max_attempts) VALUES (?, ?, ?, ?)",
                                (task_id, task["owner"], task["acceptance"], attempts))
            for task_id, task in tasks.items():
                self.db.executemany("INSERT INTO dependencies VALUES (?, ?)",
                                    ((task_id, item) for item in task.get("depends", [])))
                self.db.executemany("INSERT INTO files VALUES (?, ?)",
                                    ((file_path(path), task_id) for path in task.get("files", [])))

    def log(self, task, action, detail):
        self.db.execute("INSERT INTO events (task, action, detail, at) VALUES (?, ?, ?, ?)",
                        (task, action, detail, time.time()))

    def recover(self):
        now = time.time()
        expired = self.db.execute("SELECT * FROM tasks WHERE state='running' AND lease <= ?", (now,)).fetchall()
        for task in expired:
            state = "pending" if task["attempts"] < task["max_attempts"] else "blocked"
            self.db.execute("UPDATE tasks SET state=?, token=NULL, lease=NULL, problem=? WHERE id=?",
                            (state, "worker lease expired", task["id"]))
            self.log(task["id"], "lease-expired", state)

    def claim(self, owner, seconds, task_id=None):
        if owner not in OWNERS or not 1 <= seconds <= 86400:
            raise ValueError("invalid owner or lease")
        with self.transaction():
            self.recover()
            row = self.db.execute("""
                SELECT t.* FROM tasks t WHERE t.state='pending' AND t.owner=?
                AND (? IS NULL OR t.id=?)
                AND NOT EXISTS (
                    SELECT 1 FROM dependencies d JOIN tasks p ON p.id=d.prerequisite
                    WHERE d.task=t.id AND p.state!='verified'
                ) ORDER BY t.rowid LIMIT 1
            """, (owner, task_id, task_id)).fetchone()
            if row is None:
                return None
            token = uuid.uuid4().hex
            self.db.execute("""UPDATE tasks SET state='running', token=?, lease=?, attempts=attempts+1
                               WHERE id=?""", (token, time.time() + seconds, row["id"]))
            self.log(row["id"], "claim", owner)
            return {"task": row["id"], "token": token, "previous_problem": row["problem"],
                    "checkpoint": json.loads(row["checkpoint"]) if row["checkpoint"] else None}

    def active(self, task_id, token):
        task = self.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not task or task["state"] != "running" or task["token"] != token or task["lease"] <= time.time():
            raise ValueError("task has no current lease for this token")
        return task

    def update(self, task_id, token, action, detail, seconds=900):
        if not detail.strip() or not 1 <= seconds <= 86400:
            raise ValueError("details and a valid lease duration required")
        with self.transaction():
            task = self.active(task_id, token)
            if action == "checkpoint":
                checkpoint = json.loads(detail)
                if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("next"), str) or not checkpoint["next"].strip():
                    raise ValueError("checkpoint requires an object with a next action")
                self.db.execute("UPDATE tasks SET checkpoint=?, lease=? WHERE id=?",
                                (detail, time.time() + seconds, task_id))
            elif action == "finish":
                self.db.execute("""UPDATE tasks SET state='verified', evidence=?, problem=NULL,
                                   token=NULL, lease=NULL WHERE id=?""", (detail, task_id))
            elif action == "fail":
                state = "pending" if task["attempts"] < task["max_attempts"] else "blocked"
                self.db.execute("UPDATE tasks SET state=?, problem=?, token=NULL, lease=NULL WHERE id=?",
                                (state, detail, task_id))
            else:
                raise ValueError("unknown update")
            self.log(task_id, action, detail)

    def reopen(self, task_id, reason):
        if not reason.strip():
            raise ValueError("recovery reason required")
        with self.transaction():
            changed = self.db.execute("""UPDATE tasks SET state='pending', max_attempts=attempts+1
                                         WHERE id=? AND state='blocked'""", (task_id,)).rowcount
            if not changed:
                raise ValueError("only blocked tasks can be reopened")
            self.log(task_id, "reopen", reason)

    def handoff(self, task_id, owner, reason):
        if owner not in OWNERS or not reason.strip():
            raise ValueError("valid owner and handoff reason required")
        with self.transaction():
            changed = self.db.execute("""UPDATE tasks SET owner=? WHERE id=? AND state IN
                                         ('pending', 'blocked')""", (owner, task_id)).rowcount
            if not changed:
                raise ValueError("handoff requires a pending or blocked task")
            self.log(task_id, "handoff", reason)

    def check_files(self, task_id, token, paths):
        self.active(task_id, token)
        owned = {row[0] for row in self.db.execute("SELECT path FROM files WHERE task=?", (task_id,))}
        denied = {file_path(path) for path in paths} - owned
        if denied:
            raise ValueError("unowned files: " + ", ".join(sorted(denied)))
        return sorted(owned)

    def status(self):
        with self.transaction():
            self.recover()
            plan = self.db.execute("SELECT * FROM plan").fetchone()
            tasks = []
            for row in self.db.execute("SELECT * FROM tasks ORDER BY rowid"):
                task = dict(row)
                del task["token"]
                task["checkpoint"] = json.loads(task["checkpoint"]) if task["checkpoint"] else None
                task["depends"] = [item[0] for item in self.db.execute(
                    "SELECT prerequisite FROM dependencies WHERE task=? ORDER BY prerequisite", (task["id"],))]
                task["files"] = [item[0] for item in self.db.execute(
                    "SELECT path FROM files WHERE task=? ORDER BY path", (task["id"],))]
                tasks.append(task)
            return {"plan": dict(plan) if plan else None, "tasks": tasks,
                    "events": [dict(row) for row in self.db.execute("SELECT * FROM events ORDER BY seq")]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=".beyin-bedava/tasks.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init").add_argument("plan", type=Path)
    commands.add_parser("status")
    claim = commands.add_parser("claim")
    claim.add_argument("owner", choices=sorted(OWNERS))
    claim.add_argument("--task")
    claim.add_argument("--seconds", type=int, default=900)
    for name in ("checkpoint", "finish", "fail", "check-files"):
        command = commands.add_parser(name)
        command.add_argument("task")
        command.add_argument("token")
        if name == "check-files":
            command.add_argument("paths", nargs="+")
        else:
            command.add_argument("detail")
        if name == "checkpoint":
            command.add_argument("--seconds", type=int, default=900)
    for name in ("reopen", "handoff"):
        command = commands.add_parser(name)
        command.add_argument("task")
        if name == "handoff":
            command.add_argument("owner", choices=sorted(OWNERS))
        command.add_argument("reason")
    args = parser.parse_args()
    try:
        ledger = Ledger(args.db)
        result = {"ok": True}
        if args.command == "init":
            ledger.init(json.loads(args.plan.read_text(encoding="utf-8")))
        elif args.command == "status":
            result = ledger.status()
        elif args.command == "claim":
            result = ledger.claim(args.owner, args.seconds, args.task)
        elif args.command == "reopen":
            ledger.reopen(args.task, args.reason)
        elif args.command == "handoff":
            ledger.handoff(args.task, args.owner, args.reason)
        elif args.command == "check-files":
            result = {"owned": ledger.check_files(args.task, args.token, args.paths)}
        else:
            ledger.update(args.task, args.token, args.command, args.detail, getattr(args, "seconds", 900))
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
