export interface Message {
  role: 'user' | 'assistant'
  text: string
}

export interface TreeNode {
  id: string
  content: string
  messages: Message[]
  parentId: string | null
  isCollapsed?: boolean
}

export interface TreeState {
  nodes: Record<string, TreeNode>
  rootId: string
  selectedNodeId: string | null
}
