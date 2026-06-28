#!/usr/bin/env python3
"""
distill_to_obsidian.py

读取最新 Claude Code session jsonl，用 Haiku 4.5 提炼结构化知识，
写入 Obsidian 记忆宫殿（追加到主题文件）+ 更新 ~/.claude/.../memory/ 对应文件。

触发方式：
  - SessionStart / Stop hook 自动调用（传 --session-id <id>）
  - /distill-to-obsidian skill 手动调用
"""

import os
import sys
import json
import argparse
import re
import glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic

# ── 路径常量 ──────────────────────────────────────────────────────────────────
PROJECTS_DIR = Path.home() / ".claude/projects/-Users-civane"
MEMORY_DIR   = PROJECTS_DIR / "memory"
OBSIDIAN_PALACE = Path("/Users/civane/Documents/Obsidian Vault/🏛️ 记忆宫殿")
STATE_FILE   = Path.home() / ".claude/scripts/.distill_state.json"
LOG_FILE     = Path.home() / ".claude/scripts/distill.log"
TREE_SESSIONS_DIR = Path.home() / "Desktop/thought-tree/public/sessions"

ROOMS = {
    "技术与工具": OBSIDIAN_PALACE / "🚪 技术与工具",
    "思考与决策": OBSIDIAN_PALACE / "🚪 思考与决策",
    "项目进展":   OBSIDIAN_PALACE / "🚪 项目进展",
    "学习与研究": OBSIDIAN_PALACE / "🚪 学习与研究",
}

# ── 日志 ──────────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── State（已处理的 session + 最后处理的行数）────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


# ── jsonl 解析：提取对话文本 ──────────────────────────────────────────────────
def extract_conversation(jsonl_path: Path, from_line: int = 0) -> tuple[list[dict], int]:
    """返回 (messages, total_lines)，messages 是 [{role, text}, ...]"""
    messages = []
    total = 0
    try:
        lines = jsonl_path.read_text(encoding="utf-8").splitlines()
        total = len(lines)
        for line in lines[from_line:]:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("type") not in ("user", "assistant"):
                continue
            msg = obj.get("message", {})
            role = msg.get("role", obj.get("type"))
            content = msg.get("content", "")
            # content 可能是 str 或 list
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_result":
                            # 跳过工具结果，太啰嗦
                            pass
                text = "\n".join(p for p in parts if p).strip()
            else:
                text = str(content).strip()
            if text and len(text) > 10:
                messages.append({"role": role, "text": text[:4000]})  # 单条截断
    except Exception as e:
        log(f"解析 {jsonl_path.name} 失败: {e}")
    return messages, total


# ── 用 Haiku 4.5 提炼 ─────────────────────────────────────────────────────────
DISTILL_SYSTEM = """你是一个知识提炼助手。用户会给你一段 Claude Code 对话记录。
请从中提炼出有价值的结构化知识，输出 JSON。

规则：
1. 只提炼有实质内容的对话；如果对话太短或无实质内容，返回 topics: []
2. 每个 topic 对应一个独立主题/项目
3. room 必须是以下之一：技术与工具 / 思考与决策 / 项目进展 / 学习与研究
4. filename 是 Obsidian 文件名（不含路径和 .md，中文或英文均可，与现有文件名保持一致）
5. memory_file 是 ~/.claude/projects/.../memory/ 下对应的文件名（如 topic_wan_ttt.md），不存在则为 null
6. content 是要追加到 Obsidian 文件的 Markdown 内容，用 ## 日期 小标题组织，简洁精炼
7. memory_content 是要更新到 memory 文件 body 的内容（frontmatter 保持不变），null 表示不更新

输出格式（严格 JSON，不要 markdown 代码块）：
{
  "topics": [
    {
      "room": "学习与研究",
      "filename": "Mem-TTT 论文",
      "memory_file": "project_mem_ttt_paper.md",
      "content": "## 2026-06-26\\n\\n- 发现 gate_bias 在 bf16 下不更新的 bug...",
      "memory_content": null
    }
  ]
}"""


def distill_with_haiku(messages: list[dict], date_str: str) -> list[dict]:
    """调用 Haiku 4.5，返回 topics 列表"""
    if not messages:
        return []

    # 构造对话摘要文本
    conv_text = ""
    for m in messages[:60]:  # 最多60条
        role_label = "用户" if m["role"] == "user" else "Claude"
        conv_text += f"\n[{role_label}]: {m['text'][:1500]}\n"

    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=DISTILL_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"今天日期：{date_str}\n\n以下是对话记录：\n{conv_text}",
                }
            ],
        )
        raw = response.content[0].text.strip()
        # 去掉可能的 markdown fence
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        return data.get("topics", [])
    except Exception as e:
        log(f"Haiku 调用失败: {e}")
        return []


# ── 写入 Obsidian ──────────────────────────────────────────────────────────────
def append_to_obsidian(topic: dict):
    room_name = topic.get("room", "")
    filename  = topic.get("filename", "").strip()
    content   = topic.get("content", "").strip()

    if not filename or not content:
        return

    room_dir = ROOMS.get(room_name)
    if not room_dir:
        log(f"未知 room: {room_name}，跳过")
        return

    room_dir.mkdir(parents=True, exist_ok=True)
    target = room_dir / f"{filename}.md"

    if target.exists():
        existing = target.read_text(encoding="utf-8")
        # 避免重复追加完全相同的内容
        if content in existing:
            log(f"内容已存在，跳过: {filename}")
            return
        updated = existing.rstrip() + "\n\n" + content + "\n"
    else:
        updated = f"# {filename}\n\n{content}\n"

    target.write_text(updated, encoding="utf-8")
    log(f"Obsidian 已更新: {room_name}/{filename}.md")

    # 更新房间索引
    update_room_index(room_dir, filename)


def update_room_index(room_dir: Path, filename: str):
    index_file = room_dir / "🗂️ 索引.md"
    link = f"[[{filename}]]"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        if link not in content:
            index_file.write_text(content.rstrip() + f"\n- {link}\n", encoding="utf-8")
    else:
        index_file.write_text(f"# 索引\n\n- {link}\n", encoding="utf-8")


# ── 更新 memory 文件 ───────────────────────────────────────────────────────────
def update_memory_file(topic: dict):
    memory_file = topic.get("memory_file")
    memory_content = topic.get("memory_content")

    if not memory_file or not memory_content:
        return

    target = MEMORY_DIR / memory_file
    if not target.exists():
        log(f"memory 文件不存在，跳过: {memory_file}")
        return

    existing = target.read_text(encoding="utf-8")

    # 保留 frontmatter，替换 body
    if existing.startswith("---"):
        end = existing.find("---", 3)
        if end != -1:
            frontmatter = existing[: end + 3]
            updated = frontmatter + "\n\n" + memory_content.strip() + "\n"
        else:
            updated = existing.rstrip() + "\n\n" + memory_content.strip() + "\n"
    else:
        updated = memory_content.strip() + "\n"

    if updated == existing:
        return

    target.write_text(updated, encoding="utf-8")
    log(f"memory 已更新: {memory_file}")


# ── 读取 thought-tree 结构化节点 ──────────────────────────────────────────────
def load_tree_nodes(session_id: str, from_version: int = 0) -> list[dict]:
    """返回 thought-tree 中比 from_version 新的节点列表，每个节点含 summary/tags。"""
    tree_file = TREE_SESSIONS_DIR / f"{session_id}.json"
    if not tree_file.exists():
        return []
    try:
        tree = json.loads(tree_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    nodes = []
    for node in tree.get("nodes", {}).values():
        if node["id"] == "root":
            continue
        # 只取有 summary 字段的节点（新格式），且版本比已处理的新
        node_ts = int(node["id"].split("_")[-1]) if "_" in node["id"] else 0
        if node_ts <= from_version:
            continue
        summary = node.get("summary", "").strip()
        if not summary:
            continue
        nodes.append({
            "id":      node["id"],
            "label":   node.get("content", ""),
            "summary": summary,
            "tags":    node.get("tags", []),
            "messages": node.get("messages", []),
        })
    # 按时间戳排序
    nodes.sort(key=lambda n: int(n["id"].split("_")[-1]) if "_" in n["id"] else 0)
    return nodes


def nodes_to_distill_input(nodes: list[dict], date_str: str) -> str:
    """把 thought-tree 节点转成喂给 Haiku 的文本，比原始 jsonl 更结构化。"""
    lines = [f"日期：{date_str}\n以下是本次会话的结构化节点摘要：\n"]
    for n in nodes:
        lines.append(f"### {n['label']}")
        lines.append(f"摘要：{n['summary']}")
        if n["tags"]:
            lines.append(f"标签：{', '.join(n['tags'])}")
        lines.append("")
    return "\n".join(lines)


# ── 主流程 ────────────────────────────────────────────────────────────────────
def find_latest_session() -> Optional[Path]:
    files = sorted(PROJECTS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def process_session(session_path: Path, state: dict) -> dict:
    session_id   = session_path.stem
    prev_state   = state.get(session_id, {})
    from_line    = prev_state.get("last_line", 0)
    from_version = prev_state.get("tree_version", 0)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 优先读 thought-tree 结构化节点
    tree_nodes = load_tree_nodes(session_id, from_version=from_version)
    if tree_nodes:
        log(f"提炼 {session_id[:8]}…（thought-tree 节点 {len(tree_nodes)} 个）")
        conv_text = nodes_to_distill_input(tree_nodes, date_str)
        # 包装成 messages 列表喂给 distill_with_haiku
        messages = [{"role": "user", "text": conv_text}]
        new_version = max(
            int(n["id"].split("_")[-1]) for n in tree_nodes if "_" in n["id"]
        )
    else:
        # fallback：从 jsonl 增量提取
        messages, total_lines = extract_conversation(session_path, from_line=from_line)
        if not messages:
            log(f"无新内容: {session_id[:8]}…")
            state[session_id] = {"last_line": total_lines, "tree_version": from_version}
            return state
        log(f"提炼 {session_id[:8]}…（jsonl fallback，{len(messages)} 条，从第 {from_line} 行）")
        new_version = from_version

    topics = distill_with_haiku(messages, date_str)

    if not topics:
        log("未提炼到有效主题")
    else:
        for topic in topics:
            append_to_obsidian(topic)
            update_memory_file(topic)
        log(f"共提炼 {len(topics)} 个主题")

    _, total_lines = extract_conversation(session_path, from_line=0)
    state[session_id] = {"last_line": total_lines, "tree_version": new_version}
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", help="指定 session id，否则处理最新 session")
    parser.add_argument("--all", action="store_true", help="处理所有未处理的 session")
    args = parser.parse_args()

    state = load_state()

    if args.all:
        paths = sorted(PROJECTS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        for p in paths:
            state = process_session(p, state)
    elif args.session_id:
        p = PROJECTS_DIR / f"{args.session_id}.jsonl"
        if p.exists():
            state = process_session(p, state)
        else:
            log(f"找不到 session: {args.session_id}")
    else:
        p = find_latest_session()
        if p:
            state = process_session(p, state)
        else:
            log("找不到任何 session 文件")

    save_state(state)


if __name__ == "__main__":
    main()
