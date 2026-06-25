import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
} from '@xyflow/react'
import type { NodeMouseHandler } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useStore } from '../store'
import { buildFlowGraph } from '../utils/layout'
import { ThoughtNode } from './TreeNode'

// Must be defined outside component to avoid remounting on re-render
const nodeTypes = { thoughtNode: ThoughtNode }

function FlowInner() {
  const nodes = useStore((s) => s.nodes)
  const rootId = useStore((s) => s.rootId)
  const selectedNodeId = useStore((s) => s.selectedNodeId)
  const selectNode = useStore((s) => s.selectNode)

  const { flowNodes, flowEdges } = useMemo(
    () => buildFlowGraph(nodes, rootId, selectedNodeId),
    [nodes, rootId, selectedNodeId]
  )

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      selectNode(node.id)
    },
    [selectNode]
  )

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onNodeClick={onNodeClick}
      fitView
      fitViewOptions={{ padding: 0.25 }}
      minZoom={0.2}
      maxZoom={2}
      proOptions={{ hideAttribution: true }}
      style={{ background: '#ede8dc' }}
    >
      <Background color="#d4cec4" gap={28} size={0.8} />
      <Controls />
      <MiniMap
        nodeColor={(n) =>
          (n.data as { isSelected?: boolean }).isSelected ? '#5c7a62' : '#cfc8b8'
        }
        style={{ background: '#f5f1e8', border: '1px solid #d4cdc0', borderRadius: 10 }}
        maskColor="rgba(237,232,220,0.75)"
      />
    </ReactFlow>
  )
}

export function TreePanel() {
  return (
    <div style={{ flex: 1, minWidth: 0, height: '100vh' }}>
      <ReactFlowProvider>
        <FlowInner />
      </ReactFlowProvider>
    </div>
  )
}
