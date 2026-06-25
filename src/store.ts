import { create } from 'zustand'
import type { TreeNode, Message } from './types'
import { mockNodes, rootId } from './mockData'
import { extractSummary } from './utils/summarize'

interface StoreState {
  nodes: Record<string, TreeNode>
  rootId: string
  selectedNodeId: string | null
  selectNode: (id: string) => void
  toggleCollapse: (id: string) => void
  addChildNode: (parentId: string, userText: string, assistantText: string) => string
  getAncestorMessages: (nodeId: string) => Message[]
  getChildren: (nodeId: string) => TreeNode[]
  loadNodes: (data: { nodes: Record<string, TreeNode>; rootId: string }) => void
}

export const useStore = create<StoreState>((set, get) => ({
  nodes: mockNodes,
  rootId,
  selectedNodeId: null,

  selectNode: (id) => set({ selectedNodeId: id }),

  toggleCollapse: (id) =>
    set((state) => ({
      nodes: {
        ...state.nodes,
        [id]: { ...state.nodes[id], isCollapsed: !state.nodes[id].isCollapsed },
      },
    })),

  addChildNode: (parentId, userText, assistantText) => {
    const id = `node_${Date.now()}`
    const content = extractSummary(assistantText)
    const newNode: TreeNode = {
      id,
      content,
      parentId,
      messages: [
        { role: 'user', text: userText },
        { role: 'assistant', text: assistantText },
      ],
    }
    set((state) => ({
      nodes: { ...state.nodes, [id]: newNode },
      selectedNodeId: id,
    }))
    return id
  },

  getAncestorMessages: (nodeId) => {
    const { nodes } = get()
    const path: TreeNode[] = []
    let current: TreeNode | undefined = nodes[nodeId]
    while (current) {
      path.unshift(current)
      current = current.parentId ? nodes[current.parentId] : undefined
    }
    return path.flatMap((n) => n.messages)
  },

  getChildren: (nodeId) => {
    const { nodes } = get()
    return Object.values(nodes).filter((n) => n.parentId === nodeId)
  },

  loadNodes: (data) =>
    set({ nodes: data.nodes, rootId: data.rootId, selectedNodeId: null }),
}))
