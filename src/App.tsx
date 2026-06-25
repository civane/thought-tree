import { useEffect, useState } from 'react'
import { TreePanel } from './components/TreePanel'
import { ChatPanel } from './components/ChatPanel'
import { useStore } from './store'
import './styles/global.css'

export default function App() {
  const loadNodes = useStore((s) => s.loadNodes)
  const [currentSession, setCurrentSession] = useState<{ sessionId: string; version: number } | null>(null)

  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch('/current.json?t=' + Date.now())
        if (!res.ok) return
        const data = await res.json()

        // Load tree if session changed or version updated
        if (!currentSession || data.sessionId !== currentSession.sessionId || data.version !== currentSession.version) {
          const treeRes = await fetch(`/sessions/${data.sessionId}.json?t=${Date.now()}`)
          if (treeRes.ok) {
            const tree = await treeRes.json()
            loadNodes(tree)
            setCurrentSession(data)
          }
        }
      } catch {}
    }
    poll()
    const id = setInterval(poll, 3000)
    return () => clearInterval(id)
  }, [loadNodes, currentSession])

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#12121f' }}>
      <TreePanel />
      <ChatPanel />
    </div>
  )
}
