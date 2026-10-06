#!/usr/bin/env python3
"""
Helper for the /daily-log Claude Code skill.

  daily_log.py collect [YYYY-MM-DD]
      Scans ~/.claude/projects/**.jsonl for sessions with activity on that day
      (local time, default today), and writes:
        ~/.config/cc-daily-log/out/<date>.md    condensed transcripts to summarize
        ~/.config/cc-daily-log/out/<date>.json  one entry per session; fill in
                                                "title" and "summary" (or "skip": true)
  daily_log.py payload [YYYY-MM-DD]
      Prints the filled-in JSON as Notion page properties (JSON) for the Notion MCP.
      Refuses (exit 2) if a title/summary looks like it contains a credential.
      Claude upserts them into the "Claude Code ログ" database, keyed by セッションID
      (= session_id:date), so re-running the same day updates the same rows.
"""
from __future__ import annotations   # macOS system python3 is 3.9

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
CONFIG_DIR = Path.home() / ".config" / "cc-daily-log"
CONFIG_PATH = CONFIG_DIR / "config.json"   # workspace-specific values stay out of the public repo
OUT_DIR = CONFIG_DIR / "out"
PER_SESSION_CHARS = 12000   # condensed transcript kept per session (head + tail)
SKILL_COMMAND = "daily-log"  # sessions that only ran this command are skipped


# ------------------------------------------------------------------ helpers
def local_day(arg: str | None) -> dt.date:
    return dt.date.fromisoformat(arg) if arg else dt.datetime.now().astimezone().date()


def parse_ts(ts: str | None) -> dt.datetime | None:
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text":
                parts.append(c.get("text", ""))
            elif c.get("type") == "tool_use":
                inp = c.get("input", {}) or {}
                target = inp.get("file_path") or inp.get("command") or inp.get("pattern") or inp.get("url") or ""
                parts.append(f"[tool:{c.get('name', '')} {str(target)[:150]}]")
    return "\n".join(p for p in parts if p)


def git(cwd: str, *args: str) -> str:
    if not cwd or not Path(cwd).is_dir():
        return ""
    try:
        out = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def repo_name(cwd: str) -> str:
    remote = git(cwd, "config", "--get", "remote.origin.url")
    if remote:
        name = remote.rstrip("/")
        if name.endswith(".git"):
            name = name[:-4]
        return "/".join(name.replace(":", "/").split("/")[-2:])
    top = git(cwd, "rev-parse", "--show-toplevel")
    return Path(top or cwd or "?").name


# ------------------------------------------------------------------ collect
def read_session(path: Path, start: dt.datetime, end: dt.datetime) -> dict | None:
    lines, prompts = [], 0
    first = last = None
    session_id = path.stem
    cwd = branch = ""
    try:
        f = path.open(encoding="utf-8")
    except OSError:
        return None
    with f:
        for raw in f:
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            ts = parse_ts(ev.get("timestamp"))
            if ts is None or not (start <= ts < end):
                continue
            session_id = ev.get("sessionId") or session_id
            cwd = ev.get("cwd") or cwd
            branch = ev.get("gitBranch") or branch
            if ev.get("isMeta") or ev.get("isSidechain"):
                continue
            msg = ev.get("message") or {}
            kind = ev.get("type")
            if kind == "user":
                content = msg.get("content")
                if isinstance(content, list) and any(
                    isinstance(c, dict) and c.get("type") == "tool_result" for c in content
                ):
                    continue
                t = text_of(content).strip()
                if not t or t.startswith("<local-command") or t.startswith("<command-message"):
                    continue
                if t.startswith("<command-name>"):
                    if SKILL_COMMAND in t:
                        continue
                    t = "（コマンド）" + t[:200]
                else:
                    prompts += 1
                first = first or ts
                last = ts
                lines.append(f"[{ts:%H:%M}] USER: {t[:2000]}")
            elif kind == "assistant":
                t = text_of(msg.get("content")).strip()
                if t:
                    first = first or ts
                    last = ts
                    lines.append(f"[{ts:%H:%M}] CLAUDE: {t[:1200]}")
    if prompts == 0:
        return None
    body = "\n".join(lines)
    if len(body) > PER_SESSION_CHARS:
        half = PER_SESSION_CHARS // 2
        body = body[:half] + "\n…（中略）…\n" + body[-half:]
    commits = ""
    if cwd:
        email = git(cwd, "config", "user.email")
        args = ["log", "--all", f"--since={first.isoformat()}", f"--until={(last + dt.timedelta(minutes=10)).isoformat()}",
                "--pretty=format:%h %s", "-n", "30"]
        if email:
            args.insert(2, f"--author={email}")
        commits = git(cwd, *args)
    return {
        "session_id": session_id,
        "repo": repo_name(cwd) if cwd else "",
        "branch": branch,
        "cwd": cwd,
        "start": first.isoformat(timespec="seconds"),
        "end": last.isoformat(timespec="seconds"),
        "prompts": prompts,
        "commits": commits,
        "body": body,
    }


def collect(day: dt.date) -> None:
    tz = dt.datetime.now().astimezone().tzinfo
    start = dt.datetime.combine(day, dt.time.min, tzinfo=tz)
    end = start + dt.timedelta(days=1)
    sessions = []
    for path in sorted(PROJECTS_DIR.glob("*/*.jsonl")):   # top level only: skips subagent transcripts
        try:
            if dt.datetime.fromtimestamp(path.stat().st_mtime, tz) < start:
                continue
        except OSError:
            continue
        s = read_session(path, start, end)
        if s:
            sessions.append(s)
    # a resumed session can live in two files; merge by session_id
    merged: dict[str, dict] = {}
    for s in sorted(sessions, key=lambda x: x["start"]):
        m = merged.get(s["session_id"])
        if m:
            m["body"] += "\n" + s["body"]
            m["prompts"] += s["prompts"]
            m["end"] = max(m["end"], s["end"])
            m["commits"] = "\n".join(x for x in (m["commits"], s["commits"]) if x)
        else:
            merged[s["session_id"]] = s
    sessions = list(merged.values())

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # transcripts quote whole conversations, so keep them away from other local users
    CONFIG_DIR.chmod(0o700)
    OUT_DIR.chmod(0o700)
    md_path, json_path = OUT_DIR / f"{day}.md", OUT_DIR / f"{day}.json"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# Claude Code セッション {day}（{len(sessions)}件）\n\n")
        for i, s in enumerate(sessions, 1):
            f.write(f"## [{i}] {s['repo'] or '-'} ({s['branch'] or '-'}) {s['start'][11:16]}–{s['end'][11:16]}\n")
            f.write(f"session_id: {s['session_id']} / cwd: {s['cwd']} / 依頼数: {s['prompts']}\n")
            f.write(f"コミット:\n{s['commits'] or '(なし)'}\n\n{s['body']}\n\n")
    entries = [{
        "index": i, "session_id": s["session_id"], "repo": s["repo"], "branch": s["branch"],
        "start": s["start"], "end": s["end"], "title": "", "summary": "", "skip": False,
    } for i, s in enumerate(sessions, 1)]
    json_path.write_text(json.dumps({"date": str(day), "sessions": entries}, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    # write_text keeps the mode of an existing file, so tighten after writing
    md_path.chmod(0o600)
    json_path.chmod(0o600)
    size = md_path.stat().st_size
    print(f"date: {day}")
    print(f"sessions: {len(sessions)}")
    print(f"transcripts: {md_path} ({size // 1024} KB)")
    print(f"fill in: {json_path}")
    for s in sessions:
        print(f"  - {s['start'][11:16]}–{s['end'][11:16]} {s['repo'] or '-'} ({s['branch'] or '-'}) 依頼{s['prompts']}件")


# ------------------------------------------------------------------ payload
TEXT_LIMIT = 1990   # Notion rich text allows 2000 chars per value

# The summaries are written by Claude; this is a mechanical last line of defence before they leave the Mac.
SECRET_PATTERNS = {
    "AWS アクセスキー": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GitHub トークン": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})"),
    "Slack トークン": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "API キー（sk-）": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "Notion トークン": re.compile(r"\b(?:secret|ntn)_[A-Za-z0-9]{40,}"),
    "Google API キー": re.compile(r"\bAIza[0-9A-Za-z_-]{35}"),
    "秘密鍵": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "パスワード等の値": re.compile(
        r"(?i)(?:\b(?:password|passwd|pwd|secret|token|api[_-]?key)|パスワード)\s*[:：=]\s*\S{4,}"),
}
# Unknown token formats: long runs mixing upper, lower and digits (hex hashes and UUIDs don't qualify)
RANDOM_RUN = re.compile(r"[A-Za-z0-9+/]{32,}")


def find_secrets(text: str) -> list[str]:
    hits = [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]
    if any(re.search(r"[A-Z]", m) and re.search(r"[a-z]", m) and re.search(r"[0-9]", m)
           for m in RANDOM_RUN.findall(text)):
        hits.append("ランダムな長い文字列")
    return hits


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"{CONFIG_PATH} がありません。"
                 '{"data_source_url": "collection://...", "report_time": "22:52"} の形式で作成してください')
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def payload(day: dt.date) -> None:
    config = load_config()
    json_path = OUT_DIR / f"{day}.json"
    if not json_path.exists():
        sys.exit(f"{json_path} がありません。先に collect を実行してください")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    pages, skipped, flagged = [], [], []
    for s in data["sessions"]:
        if s.get("skip"):
            skipped.append({"index": s["index"], "reason": "skip"})
            continue
        if not s.get("title") or not s.get("summary"):
            skipped.append({"index": s["index"], "reason": "title/summary が空"})
            continue
        hits = find_secrets(f"{s['title']}\n{s['summary']}")
        if hits:
            flagged.append((s["index"], hits))
            continue
        props = {
            "タイトル": s["title"][:TEXT_LIMIT],
            "リポジトリ": s.get("repo", "")[:TEXT_LIMIT],
            "ブランチ": s.get("branch", "")[:TEXT_LIMIT],
            "要約": s["summary"][:TEXT_LIMIT],
            "セッションID": f"{s['session_id']}:{data['date']}",
            "date:日時:start": s["start"],
            "date:日時:is_datetime": 1,
        }
        if s["end"] != s["start"]:
            props["date:日時:end"] = s["end"]
        pages.append({"index": s["index"], "properties": props})
    if flagged:
        # report only the kind of match, never the matched text itself
        for index, hits in flagged:
            print(f"✗ [{index}] 秘密情報の可能性: {'、'.join(hits)}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps({
        "data_source_url": config["data_source_url"],
        "report_time": config.get("report_time", ""),
        "key_suffix": f":{data['date']}",
        "pages": pages,
        "skipped": skipped,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("collect", "payload"):
        sys.exit("usage: daily_log.py collect|payload [YYYY-MM-DD]")
    day = local_day(sys.argv[2] if len(sys.argv) > 2 else None)
    collect(day) if sys.argv[1] == "collect" else payload(day)
