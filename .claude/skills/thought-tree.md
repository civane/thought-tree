# thought-tree

打开思维树，把当前 Claude Code 会话可视化为生长的节点树。

## 触发方式

用户说 "thought tree"、"思维树"、"打开树"、或 `/thought-tree`。

## 执行步骤

### Step 1：检查 dev server 是否在跑
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ 2>/dev/null
```
- 返回 `200` → 已在运行，跳到 Step 3
- 其他 → 执行 Step 2

### Step 2：启动 dev server
```bash
cd ~/Desktop/thought-tree && npm run dev > /tmp/thought-tree-dev.log 2>&1 &
```
等待约 3 秒确认启动：
```bash
sleep 3 && grep -q "Local:" /tmp/thought-tree-dev.log && echo "ready"
```

### Step 3：同步当前会话到树
```bash
python3 ~/.claude/scripts/sync_to_thought_tree.py 2>&1
```
告知用户同步结果（新增了哪个节点，或"已是最新"）。

### Step 4：告知用户
回复：**思维树已就绪：http://localhost:5173/**

说明：
- 每次 Claude Code 回复后会自动同步（Stop hook 已配置）
- 点击节点可在右侧面板追问，追问会作为子节点生长
- 话题偏移时自动在根节点旁创建新分支
