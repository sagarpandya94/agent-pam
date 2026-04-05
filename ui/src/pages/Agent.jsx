import { useState, useRef, useEffect } from 'react'
import { getCredentials } from '../api/vault'
import { runTaskStream } from '../api/agent'
import { Terminal, Play, Square, ChevronRight } from 'lucide-react'

const S = {
  heading: { fontFamily: "'Space Mono', monospace", fontSize: 20, color: '#fbbf24', marginBottom: 4 },
  sub: { fontSize: 13, color: '#4a4a6a', marginBottom: 28 },
  input: { width: '100%', background: '#0a0a0f', border: '1px solid #1e1e2e', borderRadius: 6, padding: '10px 14px', color: '#e2e8f0', fontSize: 13, outline: 'none', resize: 'vertical', minHeight: 80 },
  select: { width: '100%', background: '#0a0a0f', border: '1px solid #1e1e2e', borderRadius: 6, padding: '10px 14px', color: '#e2e8f0', fontSize: 13, outline: 'none', cursor: 'pointer' },
  label: { fontSize: 11, color: '#4a4a6a', fontFamily: "'Space Mono', monospace", marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1, display: 'block' },
}

const EVENT_COLORS = {
  stream: '#e2e8f0',
  tool: '#fbbf24',
  result: '#38bdf8',
  done: '#34d399',
  error: '#fb7185',
}

export default function AgentPage() {
  const [creds, setCreds] = useState([])
  const [task, setTask] = useState('')
  const [credId, setCredId] = useState('prod-ec2-001')
  const [running, setRunning] = useState(false)
  const [lines, setLines] = useState([])
  const termRef = useRef(null)

  useEffect(() => {
    getCredentials().then(c => { setCreds(c); if(c.length) setCredId(c[0].id) }).catch(() => {})
  }, [])

  useEffect(() => {
    if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight
  }, [lines])

  const addLine = (type, text) => setLines(prev => [...prev, { type, text, ts: new Date().toISOString() }])

  const run = async () => {
    if (!task.trim() || running) return
    setLines([])
    setRunning(true)
    addLine('meta', `> Task: ${task}`)
    addLine('meta', `> Credential: ${credId}`)
    addLine('meta', '─'.repeat(50))

    try {
      await runTaskStream(task, credId, (event) => {
        if (event.type === 'stream') {
          const text = event.content
          if (text.includes('[Tool:')) addLine('tool', text)
          else if (text.includes('[Result:')) addLine('result', text)
          else if (text.trim()) addLine('stream', text)
        } else if (event.type === 'done') {
          addLine('meta', '─'.repeat(50))
          addLine('done', '✓ Task complete')
        } else if (event.type === 'error') {
          addLine('error', `✗ Error: ${event.content}`)
        }
      })
    } catch(e) {
      addLine('error', `✗ ${e.message}`)
    }
    setRunning(false)
  }

  const EXAMPLES = [
    'Check disk usage and report any filesystems over 80%',
    'List all files in /home/ubuntu',
    'Show system uptime and load average',
    'Check memory usage',
  ]

  return (
    <div className="animate-fade-in">
      <h1 style={S.heading}>AGENT RUNNER</h1>
      <p style={S.sub}>Dispatch tasks to the Claude PAM agent — credentials are checked out automatically</p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32 }}>
        {/* Left — Task form */}
        <div>
          <div style={{ marginBottom: 16 }}>
            <label style={S.label}>Target Credential</label>
            <select style={S.select} value={credId} onChange={e => setCredId(e.target.value)}>
              {creds.length === 0
                ? <option value="prod-ec2-001">prod-ec2-001</option>
                : creds.map(c => <option key={c.id} value={c.id}>{c.id} — {c.name}</option>)
              }
            </select>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={S.label}>Task Description</label>
            <textarea style={S.input} placeholder="Describe what you want the agent to do on the target machine..."
              value={task} onChange={e => setTask(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) run() }} />
            <div style={{ fontSize: 11, color: '#2a2a3a', marginTop: 4 }}>⌘+Enter to run</div>
          </div>

          <button
            onClick={run}
            disabled={running || !task.trim()}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '10px 20px', borderRadius: 6, cursor: running ? 'not-allowed' : 'pointer',
              background: running ? '#fbbf2410' : '#fbbf2418',
              border: '1px solid #fbbf2440', color: '#fbbf24',
              fontFamily: "'Space Mono', monospace", fontSize: 12,
              opacity: running ? 0.6 : 1, transition: 'all 0.15s',
            }}>
            {running
              ? <><span style={{ display:'inline-block' }} className="animate-spin">⟳</span> Running...</>
              : <><Play size={12} /> Run Task</>
            }
          </button>

          {/* Example tasks */}
          <div style={{ marginTop: 28 }}>
            <div style={{ ...S.label, marginBottom: 10 }}>EXAMPLE TASKS</div>
            {EXAMPLES.map((ex, i) => (
              <button key={i} onClick={() => setTask(ex)}
                style={{ display:'flex', alignItems:'center', gap:8, width:'100%', textAlign:'left',
                  padding:'8px 12px', marginBottom:6, borderRadius:6, cursor:'pointer',
                  background:'#12121a', border:'1px solid #1e1e2e', color:'#6b7280', fontSize:12,
                  transition:'all 0.15s' }}
                onMouseEnter={e => { e.currentTarget.style.color='#e2e8f0'; e.currentTarget.style.borderColor='#2a2a4a' }}
                onMouseLeave={e => { e.currentTarget.style.color='#6b7280'; e.currentTarget.style.borderColor='#1e1e2e' }}>
                <ChevronRight size={12} color="#fbbf24" /> {ex}
              </button>
            ))}
          </div>
        </div>

        {/* Right — Terminal output */}
        <div>
          <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:10 }}>
            <Terminal size={14} color="#fbbf24" />
            <span style={{ fontFamily:"'Space Mono',monospace", fontSize:11, color:'#fbbf24', letterSpacing:1 }}>AGENT OUTPUT</span>
            {running && <span style={{ marginLeft:'auto', fontSize:11, color:'#34d399', fontFamily:"'Space Mono',monospace" }}>● LIVE</span>}
          </div>
          <div ref={termRef} style={{
            background:'#050508', border:'1px solid #1e1e2e', borderRadius:8,
            padding:16, height:480, overflowY:'auto', fontFamily:"'Space Mono',monospace", fontSize:11,
          }}>
            {lines.length === 0
              ? <span style={{ color:'#2a2a3a' }}>Awaiting task...<span className="cursor-blink">_</span></span>
              : lines.map((l, i) => (
                <div key={i} style={{
                  color: l.type === 'meta' ? '#2a2a4a'
                    : l.type === 'tool' ? '#fbbf24'
                    : l.type === 'result' ? '#38bdf8'
                    : l.type === 'done' ? '#34d399'
                    : l.type === 'error' ? '#fb7185'
                    : '#9ca3af',
                  marginBottom: 4, lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word'
                }}>{l.text}</div>
              ))
            }
            {running && <span style={{ color:'#fbbf24' }} className="cursor-blink">_</span>}
          </div>
        </div>
      </div>
    </div>
  )
}
