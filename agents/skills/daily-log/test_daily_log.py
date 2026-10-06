"""Run: python3 -m unittest discover -s ~/.agents/skills/daily-log"""
from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import daily_log

TZ = dt.datetime.now().astimezone().tzinfo
TODAY = dt.datetime.now().astimezone().date()
YESTERDAY = TODAY - dt.timedelta(days=1)


def at(day: dt.date, hour: int, minute: int) -> str:
    return dt.datetime.combine(day, dt.time(hour, minute), tzinfo=TZ).isoformat()


def write_jsonl(path: Path, events: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")
    return path


def codex_meta(ts: str, session_id: str, cwd: str, **extra) -> dict:
    payload = {"session_id": session_id, "id": session_id, "cwd": cwd, "source": "vscode", "thread_source": "user"}
    payload.update(extra)
    return {"timestamp": ts, "type": "session_meta", "payload": payload}


def codex_item(ts: str, item: dict) -> dict:
    return {"timestamp": ts, "type": "event_msg", "payload": {"type": "item_completed", "item": item}}


def codex_user(ts: str, text: str) -> dict:
    return codex_item(ts, {"type": "UserMessage", "content": [{"type": "text", "text": text}]})


def codex_agent(ts: str, text: str) -> dict:
    return codex_item(ts, {"type": "AgentMessage", "content": [{"type": "Text", "text": text}]})


class GatherCodexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.claude_dir = root / "claude"
        self.codex_dir = root / "codex"
        self.cwd = root / "work"
        self.cwd.mkdir()
        self.claude_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def codex_file(self, day: dt.date, name: str, events: list[dict]) -> Path:
        return write_jsonl(self.codex_dir / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}" / f"rollout-{name}.jsonl", events)

    def gather(self) -> list[dict]:
        return daily_log.gather_sessions(TODAY, self.claude_dir, self.codex_dir)

    def test_collects_user_session_with_git_metadata(self):
        self.codex_file(TODAY, "a", [
            codex_meta(at(TODAY, 10, 0), "codex-1", str(self.cwd),
                       git={"branch": "feat/x", "repository_url": "https://github.com/me/proj.git"}),
            {"timestamp": at(TODAY, 10, 0), "type": "response_item",
             "payload": {"type": "message", "role": "user",
                         "content": [{"type": "input_text", "text": "# AGENTS.md instructions"}]}},
            codex_user(at(TODAY, 10, 1), "テストを直して"),
            codex_item(at(TODAY, 10, 2), {"type": "CommandExecution", "command": ["/bin/zsh", "-lc", "make test"]}),
            codex_agent(at(TODAY, 10, 3), "直しました"),
        ])
        [s] = self.gather()
        self.assertEqual(s["tool"], "Codex")
        self.assertEqual(s["session_id"], "codex-1")
        self.assertEqual(s["repo"], "me/proj")
        self.assertEqual(s["branch"], "feat/x")
        self.assertEqual(s["prompts"], 1)
        self.assertIn("USER: テストを直して", s["body"])
        self.assertIn("CODEX: 直しました", s["body"])
        self.assertIn("make test", s["body"])
        self.assertNotIn("AGENTS.md", s["body"])

    def test_skips_subagent_and_guardian_sessions(self):
        self.codex_file(TODAY, "guardian", [
            codex_meta(at(TODAY, 11, 0), "g", str(self.cwd),
                       source={"subagent": {"other": "guardian"}}, thread_source="guardian_review"),
            codex_user(at(TODAY, 11, 1), "assess this"),
        ])
        self.assertEqual(self.gather(), [])

    def test_skips_session_that_only_runs_daily_log(self):
        self.codex_file(TODAY, "self", [
            codex_meta(at(TODAY, 18, 0), "self", str(self.cwd)),
            codex_item(at(TODAY, 18, 1), {"type": "UserMessage", "content": [
                {"type": "text", "text": "$daily-log"},
                {"type": "skill", "name": "daily-log", "path": "/x/daily-log/SKILL.md"},
            ]}),
            codex_agent(at(TODAY, 18, 2), "送りました"),
        ])
        self.assertEqual(self.gather(), [])

    def test_keeps_only_target_day_of_session_crossing_midnight(self):
        self.codex_file(YESTERDAY, "late", [
            codex_meta(at(YESTERDAY, 23, 50), "late", str(self.cwd)),
            codex_user(at(YESTERDAY, 23, 51), "昨日の依頼"),
            codex_user(at(TODAY, 0, 10), "今日の依頼"),
        ])
        [s] = self.gather()
        self.assertEqual(s["prompts"], 1)
        self.assertIn("今日の依頼", s["body"])
        self.assertNotIn("昨日の依頼", s["body"])

    def test_falls_back_to_cwd_name_without_git_metadata(self):
        self.codex_file(TODAY, "nogit", [
            codex_meta(at(TODAY, 9, 0), "nogit", str(self.cwd), git=None),
            codex_user(at(TODAY, 9, 1), "質問"),
        ])
        [s] = self.gather()
        self.assertEqual(s["repo"], "work")
        self.assertEqual(s["branch"], "")

    def test_collects_claude_and_codex_sorted_by_start(self):
        write_jsonl(self.claude_dir / "proj" / "claude-1.jsonl", [
            {"timestamp": at(TODAY, 8, 0), "type": "user", "sessionId": "claude-1", "cwd": str(self.cwd),
             "gitBranch": "main", "message": {"content": "調べて"}},
            {"timestamp": at(TODAY, 8, 1), "type": "assistant", "sessionId": "claude-1",
             "message": {"content": [{"type": "text", "text": "調べました"}]}},
        ])
        self.codex_file(TODAY, "b", [
            codex_meta(at(TODAY, 9, 0), "codex-2", str(self.cwd)),
            codex_user(at(TODAY, 9, 1), "実装して"),
        ])
        sessions = self.gather()
        self.assertEqual([s["tool"] for s in sessions], ["Claude Code", "Codex"])
        self.assertIn("CLAUDE: 調べました", sessions[0]["body"])


class PagePropertiesTest(unittest.TestCase):
    def test_includes_tool(self):
        entry = {"tool": "Codex", "session_id": "x", "repo": "me/proj", "branch": "main",
                 "title": "t", "summary": "- s", "start": at(TODAY, 9, 0), "end": at(TODAY, 10, 0)}
        props = daily_log.page_properties(entry, str(TODAY))
        self.assertEqual(props["ツール"], "Codex")
        self.assertEqual(props["セッションID"], f"x:{TODAY}")
        self.assertEqual(props["date:日時:end"], entry["end"])


if __name__ == "__main__":
    unittest.main()
