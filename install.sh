#!/bin/bash
# Thought Tree 安装脚本

set -e

echo "🌳 Installing Thought Tree..."

# 1. 复制同步脚本
mkdir -p ~/.claude/scripts
cp scripts/sync_to_thought_tree.py ~/.claude/scripts/
chmod +x ~/.claude/scripts/sync_to_thought_tree.py
echo "✓ Sync script installed"

# 2. 复制 skill
mkdir -p ~/.claude/skills
cp .claude/skills/thought-tree.md ~/.claude/skills/
echo "✓ Skill installed"

# 3. 安装前端依赖
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

# 4. 检查 Stop hook
SETTINGS=~/.claude/settings.json
if [ -f "$SETTINGS" ]; then
  if ! grep -q "sync_to_thought_tree.py" "$SETTINGS"; then
    echo ""
    echo "⚠️  需要手动添加 Stop hook 到 ~/.claude/settings.json："
    echo ""
    echo '在 "hooks": { "Stop": [{"matcher": "", "hooks": [...这里添加]}] } 中添加：'
    echo ""
    echo '  {'
    echo '    "type": "command",'
    echo '    "command": "python3 ~/.claude/scripts/sync_to_thought_tree.py >> ~/.claude/scripts/tree_sync.log 2>&1"'
    echo '  }'
    echo ""
  else
    echo "✓ Stop hook already configured"
  fi
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  1. 在 Claude Code 中运行: /thought-tree"
echo "  2. 或手动启动: npm run dev"
echo "  3. 打开浏览器: http://localhost:5173"
