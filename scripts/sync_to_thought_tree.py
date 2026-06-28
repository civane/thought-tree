#!/usr/bin/env python3
"""Sync latest Claude Code exchange to thought tree on Stop hook."""

import json
import urllib.request
import sys
from pathlib import Path
from datetime import datetime

SESSIONS_DIR = Path.home() / ".claude" / "projects" / "-Users-civane"
PUBLIC_DIR   = Path.home() / "Desktop" / "thought-tree" / "public"
SESSIONS_OUT = PUBLIC_DIR / "sessions"
CURRENT_FILE = PUBLIC_DIR / "current.json"
INDEX_FILE   = PUBLIC_DIR / "sessions_index.json"
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


def topic_changed(recent_summaries: list, new_text: str, cfg: dict) -> bool:
    """Use Haiku to semantically judge if new_text starts a new topic."""
    if not recent_summaries:
        return False
    context = "、".join(recent_summaries[-3:])
    prompt = (
        "判断新问答是否切换了话题，输出严格 JSON（不要 markdown 代码块）：\n"
        '{"new_topic": true或false, "topic_label": "新话题标题（如果是新话题）"}\n\n'
        f"当前话题上下文：{context[:300]}\n\n"
        f"新问答：{new_text[:300]}"
    )
    try:
        raw = call_api(prompt, cfg, max_tokens=80)
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        data = json.loads(raw)
        return bool(data.get("new_topic", False)), str(data.get("topic_label", ""))
    except Exception as e:
        print(f"Topic detection failed ({e}), fallback to Jaccard", file=sys.stderr)
        # fallback to original Jaccard
        ctx = extract_tokens(' '.join(recent_summaries[-4:]))
        new = extract_tokens(new_text[:400])
        if not ctx or not new:
            return False, ""
        jaccard = len(ctx & new) / len(ctx | new)
        return jaccard < 0.08, first_sentence(new_text, 16)


def call_api(prompt: str, cfg: dict, max_tokens: int = 200) -> str:
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
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


def summarize_via_api(user_text: str, assistant_text: str, cfg: dict) -> dict:
    prompt = (
        "分析这段问答，输出严格 JSON（不要 markdown 代码块）：\n"
        '{"label":"15字内的树节点标题","summary":"50字内的核心结论，供知识库使用","tags":["标签1","标签2"]}\n\n'
        f"问：{user_text[:300]}\n\n答：{assistant_text[:600]}"
    )
    raw = call_api(prompt, cfg, max_tokens=200)
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    data = json.loads(raw)
    return {
        "label":   str(data.get("label", ""))[:20],
        "summary": str(data.get("summary", ""))[:200],
        "tags":    [str(t) for t in data.get("tags", [])][:5],
    }


def summarize(user_text: str, assistant_text: str, cfg: dict) -> dict:
    try:
        return summarize_via_api(user_text, assistant_text, cfg)
    except Exception as e:
        print(f"API summary failed ({e}), using fallback", file=sys.stderr)
        label = first_sentence(assistant_text)
        return {"label": label, "summary": label, "tags": []}


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


def load_tree(session_id: str) -> dict:
    tree_file = SESSIONS_OUT / f"{session_id}.json"
    if tree_file.exists():
        return json.loads(tree_file.read_text(encoding="utf-8"))
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

    tree = load_tree(session_id)
    for node in tree["nodes"].values():
        for msg in node.get("messages", []):
            if msg.get("role") == "user" and msg.get("text", "").startswith(user_text[:50]):
                print("Already in tree.")
                state[session_id] = mtime
                save_state(state)
                return

    cfg = get_api_config()
    meta = summarize(user_text, assistant_text, cfg)

    # Collect recent branch summaries for topic detection
    recent: list = []
    cur = tree["nodes"].get(tree["lastNodeId"])
    for _ in range(5):
        if not cur or cur["id"] == "root":
            break
        recent.append(cur.get("summary", cur["content"]) + " ".join(
            m.get("text", "")[:80] for m in cur.get("messages", [])
        ))
        cur = tree["nodes"].get(cur.get("parentId", ""))
    recent.reverse()

    parent_id = tree["lastNodeId"]

    # Topic shift detected → create a new parallel parent under root
    ts = int(datetime.now().timestamp() * 1000)
    if recent:
        is_new_topic, topic_label = topic_changed(recent, user_text + " " + assistant_text, cfg)
        if is_new_topic:
            topic_id = f"topic_{ts}"
            label = topic_label or first_sentence(user_text, 16)
            tree["nodes"][topic_id] = {
                "id":       topic_id,
                "content":  "话题：" + label,
                "summary":  label,
                "tags":     [],
                "parentId": "root",
                "messages": [],
            }
            parent_id = topic_id
            print(f"Topic shift → new branch: {tree['nodes'][topic_id]['content']}")

    node_id = f"node_{int(datetime.now().timestamp() * 1000)}"
    tree["nodes"][node_id] = {
        "id":       node_id,
        "content":  meta["label"],
        "summary":  meta["summary"],
        "tags":     meta["tags"],
        "parentId": parent_id,
        "messages": [
            {"role": "user",      "text": user_text},
            {"role": "assistant", "text": assistant_text},
        ],
    }
    tree["lastNodeId"] = node_id
    tree["version"]    = int(datetime.now().timestamp() * 1000)

    # Save session tree
    SESSIONS_OUT.mkdir(parents=True, exist_ok=True)
    session_file = SESSIONS_OUT / f"{session_id}.json"
    session_file.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update current.json
    CURRENT_FILE.write_text(json.dumps({
        "sessionId": session_id,
        "version": tree["version"],
    }, ensure_ascii=False), encoding="utf-8")

    # Update sessions index
    index = []
    if INDEX_FILE.exists():
        index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

    # Find or add this session in index
    found = False
    for entry in index:
        if entry["id"] == session_id:
            entry["updatedAt"] = tree["version"]
            found = True
            break

    if not found:
        # Get first user message as title
        title = first_sentence(user_text, 20) if tree["nodes"]["root"].get("messages") else "New Session"
        index.append({
            "id": session_id,
            "title": title,
            "startedAt": tree["version"],
            "updatedAt": tree["version"],
        })

    # Sort by updatedAt descending
    index.sort(key=lambda x: x["updatedAt"], reverse=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    state[session_id] = mtime
    save_state(state)
    print(f"Added: {meta['label']} | {meta['summary']}")


if __name__ == "__main__":
    main()
