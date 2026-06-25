import dagre from 'dagre'
import type { Node, Edge } from '@xyflow/react'
import type { TreeNode } from '../types'

const NODE_WIDTH = 240
const NODE_HEIGHT = 90

export function buildFlowGraph(
  nodes: Record<string, TreeNode>,
  rootId: string,
  selectedNodeId: string | null
): { flowNodes: Node[]; flowEdges: Edge[] } {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 50, ranksep: 90, marginx: 40, marginy: 40 })

  // BFS, skip collapsed subtrees
  const visible = new Set<string>()
  const queue = [rootId]
  while (queue.length) {
    const id = queue.shift()!
    visible.add(id)
    const node = nodes[id]
    if (!node.isCollapsed) {
      Object.values(nodes)
        .filter((n) => n.parentId === id)
        .forEach((n) => queue.push(n.id))
    }
  }

  visible.forEach((id) => {
    g.setNode(id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  })

  visible.forEach((id) => {
    const node = nodes[id]
    if (node.parentId && visible.has(node.parentId)) {
      g.setEdge(node.parentId, id)
    }
  })

  dagre.layout(g)

  const flowNodes: Node[] = [...visible].map((id) => {
    const { x, y } = g.node(id)
    const node = nodes[id]
    const hasChildren = Object.values(nodes).some((n) => n.parentId === id)
    return {
      id,
      type: 'thoughtNode',
      position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 },
      data: {
        node,
        isSelected: id === selectedNodeId,
        hasChildren,
      },
    }
  })

  const flowEdges: Edge[] = [...visible]
    .filter((id) => nodes[id].parentId && visible.has(nodes[id].parentId!))
    .map((id) => ({
      id: `e_${nodes[id].parentId}_${id}`,
      source: nodes[id].parentId!,
      target: id,
      type: 'smoothstep',
      style: { stroke: '#b8c8bc', strokeWidth: 1.5 },
      animated: false,
    }))

  return { flowNodes, flowEdges }
}
