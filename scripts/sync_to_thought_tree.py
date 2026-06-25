#!/usr/bin/env python3
"""Sync latest Claude Code exchange to thought tree on Stop hook."""

import json
import urllib.request
import sys
from pathlib import Path
from datetime import datetime

SESSIONS_DIR = Path.home() / ".claude" / "projects" / "-Users-civane"
TREE_DATA    = Path.home() / "Desktop" / "thought-tree" / "public" / "tree_data.json"
STATE_FILE   = Path.home() / ".claude" / "scripts" / ".tree_sync_state.json"

_SKIP_PHRASES = [
    "Cette session est la suite",
    "Continue the conversation from where",
    "CONTEXT ENTRY BEGIN",
    "system-reminder",
    "USER MESSAGE BEGIN",
]


def is_substantive(user_text: str, assistant_text: str) -> bool:
    if len(user_text.strip()) < 15 or len(assistant_text.strip()) < 30:
        return False
    for p in _SKIP_PHRASES:
        if p in user_text:
            return False
    return True


def first_sentence(text: str, max_len: int = 28) -> str:
    for sep in ('。', '！', '？', '\n', '.', '!', '?'):
        part = text.split(sep)[0].strip()
        if len(part) >= 8:
            s = part
            break
    else:
        s = text.strip()
    return s if len(s) <= max_len else s[:max_len] + '…'


def get_api_config():
    s = json.loads((Path.home() / ".claude" / "settings.json").read_text())
    return {
        "key":  s["env"]["ANTHROPIC_API_KEY"],
        "base": s["env"].get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/"),
    }


def extract_tokens(text: str) -> set:
    import re
    parts = re.split(r'[\s，。！？、：；,.!?:;()（）\[\]【】\n]+', text)
    return {p for p in parts if len(p) >= 2}


def topic_changed(recent_summaries: list, new_text: str) -> bool:
    """True if new_text has very low token overlap with recent branch content."""
    if not recent_summaries:
        return False
    ctx = extract_tokens(' '.join(recent_summaries[-4:]))
    new = extract_tokens(new_text[:400])
    if not ctx or not new:
        return False
    jaccard = len(ctx & new) / len(ctx | new)
    return jaccard < 0.08


def summarize_via_api(user_text: str, assistant_text: str, cfg: dict) -> str:
    prompt = (
        f"用一句话（15字以内）概括这段问答的核心观点，只输出那句话：\n\n"
        f"问：{user_text[:300]}\n\n答：{assistant_text[:400]}"
    )
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 60,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        f"{cfg['base']}/v1/messages",
        data=payload,
        headers={
            "Authorization": f"Bearer {cfg['key']}",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())["content"][0]["text"].strip()


def summarize(user_text: str, assistant_text: str, cfg: dict) -> str:
    try:
        return summarize_via_api(user_text, assistant_text, cfg)
    except Exception as e:
        print(f"API summary failed ({e}), using first sentence", file=sys.stderr)
        return first_sentence(assistant_text)


def parse_last_exchange(path: Path):
    turns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("type") in ("user", "assistant"):
            role = obj["type"]
            raw  = obj.get("message", {}).get("content", "")
        else:
            msg  = obj.get("message", {})
            role = msg.get("role")
            if role not in ("user", "assistant"):
                continue
            raw = msg.get("content", "")
        if isinstance(raw, list):
            text = "\n".join(
                b.get("text", "") for b in raw
                if isinstance(b, dict) and b.get("type") == "text"
            ).strip()
        else:
            text = str(raw).strip()
        if text:
            turns.append((role, text))
    for i in range(len(turns) - 1, 0, -1):
        if turns[i][0] == "assistant" and turns[i - 1][0] == "user":
            return turns[i - 1][1], turns[i][1]
    return None


def load_tree() -> dict:
    if TREE_DATA.exists():
        return json.loads(TREE_DATA.read_text(encoding="utf-8"))
    return {
        "nodes": {"root": {"id": "root", "content": "Claude Code 对话", "parentId": None, "messages": []}},
        "rootId": "root",
        "lastNodeId": "root",
        "version": 0,
    }


def load_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def save_state(s: dict):
    STATE_FILE.write_text(json.dumps(s, indent=2))


def main():
    files = sorted(
        (f for f in SESSIONS_DIR.glob("*.jsonl") if not f.stem.startswith("agent-")),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    if not files:
        return

    session_file = files[0]
    session_id   = session_file.stem
    mtime        = str(session_file.stat().st_mtime)

    state = load_state()
    if state.get(session_id) == mtime:
        print("No changes.")
        return

    exchange = parse_last_exchange(session_file)
    if not exchange:
        state[session_id] = mtime
        save_state(state)
        return
    user_text, assistant_text = exchange

    if not is_substantive(user_text, assistant_text):
        print("Skipped: not substantive.")
        state[session_id] = mtime
        save_state(state)
        return

    tree = load_tree()
    for node in tree["nodes"].values():
        for msg in node.get("messages", []):
            if msg.get("role") == "user" and msg.get("text", "").startswith(user_text[:50]):
                print("Already in tree.")
                state[session_id] = mtime
                save_state(state)
                return

    cfg = get_api_config()
    label = summarize(user_text, assistant_text, cfg)

    # Collect recent branch summaries for topic detection
    recent: list = []
    cur = tree["nodes"].get(tree["lastNodeId"])
    for _ in range(5):
        if not cur or cur["id"] == "root":
            break
        recent.append(cur["content"] + " ".join(
            m.get("text", "")[:80] for m in cur.get("messages", [])
        ))
        cur = tree["nodes"].get(cur.get("parentId", ""))
    recent.reverse()

    active_node_file = TREE_DATA.parent / "active_node.json"
    parent_id = tree["lastNodeId"]
    if active_node_file.exists():
        try:
            parent_id = json.loads(active_node_file.read_text()).get("nodeId") or parent_id
        except Exception:
            pass

    # Topic shift detected → create a new parallel parent under root
    ts = int(datetime.now().timestamp() * 1000)
    if recent and topic_changed(recent, user_text + " " + assistant_text):
        topic_id = f"topic_{ts}"
        tree["nodes"][topic_id] = {
            "id":       topic_id,
            "content":  "话题：" + first_sentence(user_text, 16),
            "parentId": "root",
            "messages": [],
        }
        parent_id = topic_id
        print(f"Topic shift → new branch: {tree['nodes'][topic_id]['content']}")

    node_id = f"node_{int(datetime.now().timestamp() * 1000)}"
    tree["nodes"][node_id] = {
        "id":       node_id,
        "content":  label,
        "parentId": parent_id,
        "messages": [
            {"role": "user",      "text": user_text},
            {"role": "assistant", "text": assistant_text},
        ],
    }
    tree["lastNodeId"] = node_id
    tree["version"]    = int(datetime.now().timestamp() * 1000)

    TREE_DATA.parent.mkdir(parents=True, exist_ok=True)
    TREE_DATA.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
    state[session_id] = mtime
    save_state(state)
    print(f"Added: {label}")


if __name__ == "__main__":
    main()
