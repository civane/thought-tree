import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { useStore } from '../store'
import type { TreeNode as TreeNodeType } from '../types'

interface NodeData {
  node: TreeNodeType
  isSelected: boolean
  hasChildren: boolean
}

export function ThoughtNode({ data }: NodeProps) {
  const { node, isSelected, hasChildren } = data as unknown as NodeData
  const toggleCollapse = useStore((s) => s.toggleCollapse)

  return (
    <div
      style={{
        width: 240,
        background: '#faf8f3',
        border: `1px solid ${isSelected ? '#5c7a62' : '#cfc8b8'}`,
        borderRadius: 20,
        padding: '14px 18px',
        cursor: 'pointer',
        boxShadow: isSelected
          ? '0 0 0 3px rgba(92,122,98,0.14), 0 4px 16px rgba(42,39,32,0.07)'
          : '0 2px 8px rgba(42,39,32,0.05)',
        transition: 'border-color 0.2s, box-shadow 0.2s',
        position: 'relative',
        userSelect: 'none',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <circle cx="5" cy="5" r="4" stroke={isSelected ? '#5c7a62' : '#a8bfae'} strokeWidth="1" />
          <circle cx="5" cy="5" r="1.5" fill={isSelected ? '#5c7a62' : '#a8bfae'} />
        </svg>
        <span style={{ fontSize: 10, color: isSelected ? '#5c7a62' : '#a09080', letterSpacing: '0.08em', fontFamily: 'system-ui, sans-serif' }}>
          观点
        </span>
      </div>

      <div
        style={{
          fontSize: 13,
          color: '#2a2720',
          lineHeight: 1.65,
          display: '-webkit-box',
          WebkitLineClamp: 3,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}
      >
        {node.content}
      </div>

      {hasChildren && (
        <button
          onClick={(e) => { e.stopPropagation(); toggleCollapse(node.id) }}
          style={{
            position: 'absolute',
            bottom: -13,
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#f5f1e8',
            border: '1px solid #cfc8b8',
            borderRadius: 20,
            color: '#7a9e7e',
            fontSize: 10,
            padding: '2px 10px',
            cursor: 'pointer',
            zIndex: 10,
            lineHeight: 1.6,
            fontFamily: 'system-ui, sans-serif',
            letterSpacing: '0.04em',
            whiteSpace: 'nowrap',
          }}
        >
          {node.isCollapsed ? '+ 展开' : '− 折叠'}
        </button>
      )}

      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  )
}
