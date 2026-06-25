import { useEffect } from 'react'
import { TreePanel } from './components/TreePanel'
import { ChatPanel } from './components/ChatPanel'
import { useStore } from './store'
import './styles/global.css'

export default function App() {
  const loadNodes = useStore((s) => s.loadNodes)

  useEffect(() => {
    let lastVersion = -1
    const poll = async () => {
      try {
        const res = await fetch('/tree_data.json?t=' + Date.now())
        if (!res.ok) return
        const data = await res.json()
        if (data.version !== lastVersion) {
          lastVersion = data.version
          loadNodes(data)
        }
      } catch {}
    }
    poll()
    const id = setInterval(poll, 3000)
    return () => clearInterval(id)
  }, [loadNodes])

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#12121f' }}>
      <TreePanel />
      <ChatPanel />
    </div>
  )
}
