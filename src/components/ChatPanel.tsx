import { useState, useRef, useEffect } from 'react'
import { useStore } from '../store'
import type { Message } from '../types'

async function callClaude(messages: Message[], userText: string): Promise<string> {
  const apiMessages = [
    ...messages.map((m) => ({ role: m.role, content: m.text })),
    { role: 'user', content: userText },
  ]
  const res = await fetch(`${import.meta.env.VITE_API_BASE}/v1/messages`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'Authorization': `Bearer ${import.meta.env.VITE_API_KEY}`,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 1024,
      system: '你是一个帮助用户深入思考问题的助手。回答要简洁有深度，100-200字左右，便于整理成思维节点。',
      messages: apiMessages,
    }),
  })
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return (await res.json()).content[0].text
}

function Bubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 14 }}>
      <div style={{
        maxWidth: '88%',
        background: isUser ? '#e8f0ea' : '#faf8f3',
        borderRadius: isUser ? '18px 18px 5px 18px' : '18px 18px 18px 5px',
        padding: '10px 15px',
        fontSize: 13.5,
        lineHeight: 1.7,
        color: '#2a2720',
        border: '1px solid',
        borderColor: isUser ? '#b8d4be' : '#ddd8cc',
      }}>
        {msg.text}
      </div>
    </div>
  )
}

export function ChatPanel() {
  const selectedNodeId = useStore((s) => s.selectedNodeId)
  const nodes = useStore((s) => s.nodes)
  const getAncestorMessages = useStore((s) => s.getAncestorMessages)
  const addChildNode = useStore((s) => s.addChildNode)

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const selectedNode = selectedNodeId ? nodes[selectedNodeId] : null
  const messages: Message[] = selectedNodeId ? getAncestorMessages(selectedNodeId) : []

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages, loading])

  const handleSend = async () => {
    if (!input.trim() || !selectedNodeId || loading) return
    const text = input.trim()
    setInput('')
    setError(null)
    setLoading(true)
    try {
      addChildNode(selectedNodeId, text, await callClaude(messages, text))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  const canSend = !!input.trim() && !!selectedNode && !loading

  return (
    <div style={{
      width: 360,
      flexShrink: 0,
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: '#f7f3ea',
      borderLeft: '1px solid #ddd8cc',
    }}>
      {/* Header */}
      <div style={{ padding: '20px 22px 16px', borderBottom: '1px solid #e4dfd4' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 7, marginBottom: 6,
        }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 1 C4 1 1 4 1 7 C1 10 4 13 7 13 C10 13 13 10 13 7 C13 4 10 1 7 1Z" stroke="#a8bfae" strokeWidth="1" fill="none"/>
            <path d="M7 4 L7 7 L9 9" stroke="#a8bfae" strokeWidth="1" strokeLinecap="round"/>
          </svg>
          <span style={{ fontSize: 10, color: '#9a8e7e', letterSpacing: '0.1em', fontFamily: 'system-ui, sans-serif' }}>
            {selectedNode ? '当前节点' : '思维追问'}
          </span>
        </div>
        <div style={{ fontSize: 14, color: '#2a2720', lineHeight: 1.5, minHeight: 20 }}>
          {selectedNode ? selectedNode.content : '点击左侧节点开始对话'}
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '18px 16px 8px', background: '#f7f3ea' }}>
        {messages.length === 0 && !selectedNode && (
          <div style={{ color: '#b0a48e', fontSize: 13, textAlign: 'center', marginTop: 48, lineHeight: 2, fontStyle: 'italic' }}>
            从左侧树中选择一个节点<br />查看对话历史或发起追问
          </div>
        )}
        {messages.map((msg, i) => <Bubble key={i} msg={msg} />)}
        {error && (
          <div style={{ color: '#8b4c3c', fontSize: 12, padding: '8px 12px', background: '#fdf0ec', border: '1px solid #e8c8c0', borderRadius: 12, margin: '8px 0' }}>
            {error}
          </div>
        )}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 14 }}>
            <div style={{ background: '#faf8f3', border: '1px solid #ddd8cc', borderRadius: '18px 18px 18px 5px', padding: '10px 18px', color: '#b0a48e', fontSize: 16, letterSpacing: 5 }}>
              · · ·
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: '12px 16px 16px', borderTop: '1px solid #e4dfd4', background: '#f0ebe0' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
            placeholder={selectedNode ? '追问…（Enter 发送）' : '请先选择一个节点'}
            disabled={!selectedNode || loading}
            rows={2}
            style={{
              flex: 1,
              background: '#faf8f3',
              border: '1px solid #cfc8b8',
              borderRadius: 14,
              padding: '9px 13px',
              color: '#2a2720',
              fontSize: 13.5,
              resize: 'none',
              outline: 'none',
              lineHeight: 1.55,
              fontFamily: 'inherit',
            }}
          />
          <button
            onClick={handleSend}
            disabled={!canSend}
            style={{
              background: 'none',
              border: `1px solid ${canSend ? '#5c7a62' : '#cfc8b8'}`,
              borderRadius: '50%',
              width: 38,
              height: 38,
              color: canSend ? '#5c7a62' : '#b0a48e',
              cursor: canSend ? 'pointer' : 'not-allowed',
              fontSize: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              transition: 'all 0.2s',
            }}
          >
            ↑
          </button>
        </div>
        <div style={{ fontSize: 10.5, color: '#b0a48e', marginTop: 7, textAlign: 'center', fontFamily: 'system-ui, sans-serif', letterSpacing: '0.04em' }}>
          追问将作为新子节点生长到树上
        </div>
      </div>
    </div>
  )
}
