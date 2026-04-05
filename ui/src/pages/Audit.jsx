import { useState, useEffect } from 'react'
import { getAuditEvents, getSessionEvents } from '../api/agent'
import { ScrollText, ChevronRight, AlertTriangle, CheckCircle, Info, XCircle, RefreshCw } from 'lucide-react'

const SEVERITY_CONFIG = {
  info:     { color: '#38bdf8', icon: Info,          label: 'INFO'     },
  warning:  { color: '#fbbf24', icon: AlertTriangle, label: 'WARN'     },
  critical: { color: '#fb7185', icon: XCircle,       label: 'CRITICAL' },
}

const EVENT_CONFIG = {
  session_checkout:   { color: '#34d399', label: 'CHECKOUT'   },
  session_checkin:    { color: '#38bdf8', label: 'CHECKIN'    },
  command_executed:   { color: '#9ca3af', label: 'EXEC'       },
  command_blocked:    { color: '#fbbf24', label: 'BLOCKED'    },
  policy_violation:   { color: '#fb7185', label: 'VIOLATION'  },
  injection_detected: { color: '#fb7185', label: 'INJECTION'  },
  ssh_error:          { color: '#fbbf24', label: 'SSH ERR'    },
  agent_error:        { color: '#fb7185', label: 'ERROR'      },
}

const S = {
  heading: { fontFamily: "'Space Mono', monospace", fontSize: 20, color: '#fbbf24', marginBottom: 4 },
  sub: { fontSize: 13, color: '#4a4a6a', marginBottom: 28 },
  badge: (color) => ({ display:'inline-flex', alignItems:'center', gap:4, fontSize:10, padding:'2px 7px', borderRadius:999, background:`${color}18`, color, fontFamily:"'Space Mono',monospace", letterSpacing:0.5 }),
}

function fmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function shortToken(t) {
  if (!t) return '—'
  return t.length > 20 ? `${t.slice(0,10)}...${t.slice(-6)}` : t
}

export default function AuditPage() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [sessionEvents, setSessionEvents] = useState([])
  const [filter, setFilter] = useState('all')

  const load = async () => {
    setLoading(true)
    try { setEvents(await getAuditEvents()) } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const openSession = async (token) => {
    if (!token) return
    setSelected(token)
    try { setSessionEvents(await getSessionEvents(token)) } catch { setSessionEvents([]) }
  }

  // Group events by token for session list
  const sessions = events.reduce((acc, e) => {
    if (!e.token) return acc
    if (!acc[e.token]) acc[e.token] = { token: e.token, events: [], start: e.timestamp }
    acc[e.token].events.push(e)
    return acc
  }, {})
  const sessionList = Object.values(sessions).sort((a,b) => new Date(b.start) - new Date(a.start))

  const filtered = filter === 'all' ? events : events.filter(e => e.severity === filter)
  const critCount = events.filter(e => e.severity === 'critical').length
  const warnCount = events.filter(e => e.severity === 'warning').length

  return (
    <div className="animate-fade-in">
      <h1 style={S.heading}>AUDIT TRAIL</h1>
      <p style={S.sub}>Session replay and anomaly detection log</p>

      {/* Stats row */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, marginBottom:28 }}>
        {[
          { label:'TOTAL EVENTS', value: events.length, color:'#e2e8f0' },
          { label:'SESSIONS', value: sessionList.length, color:'#38bdf8' },
          { label:'WARNINGS', value: warnCount, color:'#fbbf24' },
          { label:'CRITICAL', value: critCount, color:'#fb7185' },
        ].map(s => (
          <div key={s.label} style={{ background:'#12121a', border:'1px solid #1e1e2e', borderRadius:8, padding:'14px 16px' }}>
            <div style={{ fontSize:10, color:'#4a4a6a', fontFamily:"'Space Mono',monospace", marginBottom:6, letterSpacing:1 }}>{s.label}</div>
            <div style={{ fontSize:24, fontFamily:"'Space Mono',monospace", color:s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'280px 1fr', gap:20 }}>
        {/* Session list */}
        <div>
          <div style={{ fontSize:11, color:'#4a4a6a', fontFamily:"'Space Mono',monospace", marginBottom:10, letterSpacing:1 }}>SESSIONS</div>
          {sessionList.length === 0
            ? <div style={{ color:'#2a2a3a', fontSize:12 }}>No sessions yet.</div>
            : sessionList.map(s => {
              const hasCritical = s.events.some(e => e.severity === 'critical')
              const hasWarning = s.events.some(e => e.severity === 'warning')
              const isActive = selected === s.token
              return (
                <div key={s.token} onClick={() => openSession(s.token)}
                  style={{ background: isActive ? '#1a1a28' : '#12121a',
                    border: `1px solid ${isActive ? '#fbbf2440' : '#1e1e2e'}`,
                    borderRadius:6, padding:'10px 12px', marginBottom:6, cursor:'pointer', transition:'all 0.15s' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:4 }}>
                    <span style={{ fontSize:10, fontFamily:"'Space Mono',monospace", color:'#6b7280' }}>{fmt(s.start)}</span>
                    {hasCritical ? <span style={S.badge('#fb7185')}>● CRITICAL</span>
                      : hasWarning ? <span style={S.badge('#fbbf24')}>⚠ WARN</span>
                      : <span style={S.badge('#34d399')}>✓ CLEAN</span>}
                  </div>
                  <div style={{ fontSize:10, color:'#2a2a4a', fontFamily:"'Space Mono',monospace" }}>{shortToken(s.token)}</div>
                  <div style={{ fontSize:11, color:'#4a4a6a', marginTop:4 }}>{s.events.length} events</div>
                </div>
              )
            })
          }
        </div>

        {/* Event detail / replay */}
        <div>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:10 }}>
            <div style={{ fontSize:11, color:'#4a4a6a', fontFamily:"'Space Mono',monospace", letterSpacing:1 }}>
              {selected ? 'SESSION REPLAY' : 'ALL EVENTS'}
            </div>
            <div style={{ display:'flex', gap:6 }}>
              {selected && <button onClick={() => { setSelected(null); setSessionEvents([]) }}
                style={{ fontSize:11, color:'#6b7280', background:'none', border:'1px solid #1e1e2e', borderRadius:4, padding:'4px 10px', cursor:'pointer' }}>
                ← All Events
              </button>}
              {['all','info','warning','critical'].map(f => (
                <button key={f} onClick={() => setFilter(f)}
                  style={{ fontSize:10, fontFamily:"'Space Mono',monospace", padding:'3px 8px', borderRadius:4, cursor:'pointer', border:'1px solid',
                    borderColor: filter===f ? '#fbbf2460' : '#1e1e2e',
                    background: filter===f ? '#fbbf2410' : 'transparent',
                    color: filter===f ? '#fbbf24' : '#4a4a6a' }}>
                  {f.toUpperCase()}
                </button>
              ))}
              <button onClick={load} style={{ background:'none', border:'1px solid #1e1e2e', borderRadius:4, padding:'4px 8px', cursor:'pointer', color:'#4a4a6a' }}>
                <RefreshCw size={11} />
              </button>
            </div>
          </div>

          <div style={{ background:'#050508', border:'1px solid #1e1e2e', borderRadius:8, height:440, overflowY:'auto' }}>
            {loading ? (
              <div style={{ padding:20, color:'#2a2a3a', fontSize:12 }}>Loading...</div>
            ) : (
              (selected ? sessionEvents : filtered).length === 0
                ? <div style={{ padding:20, color:'#2a2a3a', fontSize:12 }}>No events.</div>
                : (selected ? sessionEvents : filtered).map((e, i) => {
                  const ev = EVENT_CONFIG[e.event_type] || { color:'#6b7280', label: e.event_type }
                  const sv = SEVERITY_CONFIG[e.severity] || SEVERITY_CONFIG.info
                  const detail = e.detail || {}
                  return (
                    <div key={e.id || i} style={{ padding:'10px 14px', borderBottom:'1px solid #0d0d14',
                      background: e.severity === 'critical' ? '#fb718508' : e.severity === 'warning' ? '#fbbf2405' : 'transparent' }}>
                      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4 }}>
                        <span style={{ fontSize:10, color:'#2a2a4a', fontFamily:"'Space Mono',monospace" }}>{fmt(e.timestamp)}</span>
                        <span style={S.badge(ev.color)}>{ev.label}</span>
                        <span style={S.badge(sv.color)}>{sv.label}</span>
                        <span style={{ fontSize:10, color:'#2a2a4a', marginLeft:'auto', fontFamily:"'Space Mono',monospace" }}>{e.agent_id}</span>
                      </div>
                      {detail.command && <div style={{ fontSize:11, fontFamily:"'Space Mono',monospace", color:'#6b7280', marginBottom:2 }}>$ {detail.command}</div>}
                      {detail.stdout_preview && <div style={{ fontSize:11, color:'#34d399', fontFamily:"'Space Mono',monospace", whiteSpace:'pre', overflow:'hidden', maxHeight:40 }}>{detail.stdout_preview}</div>}
                      {detail.reason && <div style={{ fontSize:11, color:'#fb7185' }}>{detail.reason}</div>}
                      {detail.text_preview && <div style={{ fontSize:11, color:'#fb7185', fontFamily:"'Space Mono',monospace" }}>{detail.text_preview}</div>}
                      {detail.task && <div style={{ fontSize:11, color:'#6b7280' }}>Task: {detail.task}</div>}
                    </div>
                  )
                })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
