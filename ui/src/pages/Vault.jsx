import { useState, useEffect } from 'react'
import { getCredentials, createCredential, deactivateCredential, getPolicies, createPolicy } from '../api/vault'
import { Key, Shield, Plus, Trash2, RefreshCw, CheckCircle, XCircle } from 'lucide-react'

const BASE = 'http://localhost:8000'

async function checkoutCredential(agentId, credentialId, taskDescription) {
  const r = await fetch(`${BASE}/checkout/`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, credential_id: credentialId, task_description: taskDescription })
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

const S = {
  heading: { fontFamily: "'Space Mono', monospace", fontSize: 20, color: '#fbbf24', marginBottom: 4 },
  sub: { fontSize: 13, color: '#4a4a6a', marginBottom: 28 },
  card: { background: '#12121a', border: '1px solid #1e1e2e', borderRadius: 8, padding: 20, marginBottom: 12 },
  label: { fontSize: 11, color: '#4a4a6a', fontFamily: "'Space Mono', monospace", marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 },
  value: { fontSize: 13, color: '#e2e8f0' },
  badge: (color) => ({ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, padding: '2px 8px', borderRadius: 999, background: `${color}15`, color, fontFamily: "'Space Mono', monospace" }),
  input: { width: '100%', background: '#0a0a0f', border: '1px solid #1e1e2e', borderRadius: 6, padding: '8px 12px', color: '#e2e8f0', fontSize: 13, outline: 'none' },
  btn: (color='#fbbf24') => ({ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 6, border: `1px solid ${color}40`, background: `${color}10`, color, fontSize: 12, cursor: 'pointer', fontFamily: "'Space Mono', monospace" }),
  row: { display: 'flex', gap: 12, marginBottom: 12 },
  col: { flex: 1 },
}

function Section({ title, icon: Icon, color='#fbbf24', children }) {
  return (
    <div style={{ marginBottom: 40 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <Icon size={16} color={color} />
        <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 13, color, letterSpacing: 1 }}>{title}</span>
      </div>
      {children}
    </div>
  )
}

export default function VaultPage() {
  const [creds, setCreds] = useState([])
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCredForm, setShowCredForm] = useState(false)
  const [showPolicyForm, setShowPolicyForm] = useState(false)
  const [credForm, setCredForm] = useState({ id:'', name:'', host:'', port:'22', username:'', password:'' })
  const [policyForm, setPolicyForm] = useState({ id:'', name:'', credential_id:'', allowed_commands:'df,du,ls,uptime', denied_commands:'rm,sudo,curl', max_session_minutes:15 })
  const [msg, setMsg] = useState(null)

  // Checkout modal state
  const [checkoutModal, setCheckoutModal] = useState(null)
  const [checkoutTask, setCheckoutTask] = useState('')
  const [checkoutResult, setCheckoutResult] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const [c, p] = await Promise.all([getCredentials(), getPolicies()])
      setCreds(c); setPolicies(p)
    } catch(e) { setMsg({type:'error', text: e.message}) }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const flash = (text, type='success') => { setMsg({type, text}); setTimeout(() => setMsg(null), 3000) }

  const submitCred = async () => {
    try {
      await createCredential(credForm)
      flash('Credential created'); setShowCredForm(false)
      setCredForm({ id:'', name:'', host:'', port:'22', username:'', password:'' })
      load()
    } catch(e) { flash(e.message, 'error') }
  }

  const submitPolicy = async () => {
    try {
      await createPolicy({
        ...policyForm,
        allowed_commands: policyForm.allowed_commands.split(',').map(s=>s.trim()).filter(Boolean),
        denied_commands: policyForm.denied_commands.split(',').map(s=>s.trim()).filter(Boolean),
        max_session_minutes: Number(policyForm.max_session_minutes),
      })
      flash('Policy created'); setShowPolicyForm(false)
      load()
    } catch(e) { flash(e.message, 'error') }
  }

  const deactivate = async (id) => {
    try { await deactivateCredential(id); flash('Deactivated'); load() }
    catch(e) { flash(e.message, 'error') }
  }

  const submitCheckout = async () => {
    try {
      const result = await checkoutCredential('manual-admin', checkoutModal, checkoutTask)
      setCheckoutResult(result)
    } catch(e) { flash(e.message, 'error') }
  }

  return (
    <div className="animate-fade-in">
      <h1 style={S.heading}>VAULT ADMIN</h1>
      <p style={S.sub}>Manage credentials and access policies</p>

      {msg && (
        <div style={{ padding: '10px 16px', borderRadius: 6, marginBottom: 20, fontSize: 13,
          background: msg.type === 'error' ? '#fb718520' : '#34d39920',
          border: `1px solid ${msg.type === 'error' ? '#fb718540' : '#34d39940'}`,
          color: msg.type === 'error' ? '#fb7185' : '#34d399' }}>
          {msg.text}
        </div>
      )}

      {/* Credentials */}
      <Section title="CREDENTIALS" icon={Key}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <span style={{ fontSize: 12, color: '#4a4a6a' }}>{creds.length} stored</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button style={S.btn('#38bdf8')} onClick={load}><RefreshCw size={12} /> Refresh</button>
            <button style={S.btn()} onClick={() => setShowCredForm(!showCredForm)}><Plus size={12} /> Add Credential</button>
          </div>
        </div>

        {showCredForm && (
          <div style={{ ...S.card, border: '1px solid #fbbf2430', marginBottom: 16 }}>
            <div style={S.row}>
              <div style={S.col}><div style={S.label}>ID</div><input style={S.input} placeholder="prod-ec2-001" value={credForm.id} onChange={e=>setCredForm({...credForm,id:e.target.value})} /></div>
              <div style={S.col}><div style={S.label}>Name</div><input style={S.input} placeholder="Production EC2" value={credForm.name} onChange={e=>setCredForm({...credForm,name:e.target.value})} /></div>
            </div>
            <div style={S.row}>
              <div style={{flex:2}}><div style={S.label}>Host</div><input style={S.input} placeholder="localhost" value={credForm.host} onChange={e=>setCredForm({...credForm,host:e.target.value})} /></div>
              <div style={{flex:1}}><div style={S.label}>Port</div><input style={S.input} placeholder="22" value={credForm.port} onChange={e=>setCredForm({...credForm,port:e.target.value})} /></div>
            </div>
            <div style={S.row}>
              <div style={S.col}><div style={S.label}>Username</div><input style={S.input} placeholder="ubuntu" value={credForm.username} onChange={e=>setCredForm({...credForm,username:e.target.value})} /></div>
              <div style={S.col}><div style={S.label}>Password</div><input style={S.input} type="password" placeholder="••••••••" value={credForm.password} onChange={e=>setCredForm({...credForm,password:e.target.value})} /></div>
            </div>
            <div style={{ display:'flex', gap:8, marginTop:8 }}>
              <button style={S.btn()} onClick={submitCred}><CheckCircle size={12}/> Save</button>
              <button style={S.btn('#6b7280')} onClick={() => setShowCredForm(false)}><XCircle size={12}/> Cancel</button>
            </div>
          </div>
        )}

        {loading ? <div style={{ color: '#4a4a6a', fontSize: 13 }}>Loading...</div> :
          creds.length === 0 ? <div style={{ color: '#4a4a6a', fontSize: 13 }}>No credentials stored.</div> :
          creds.map(c => (
            <div key={c.id} style={S.card}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
                <div>
                  <div style={{ fontFamily:"'Space Mono',monospace", fontSize:13, color:'#fbbf24', marginBottom:4 }}>{c.id}</div>
                  <div style={{ fontSize:12, color:'#6b7280', marginBottom:8 }}>{c.name}</div>
                  <div style={{ display:'flex', gap:16 }}>
                    <span style={S.badge('#38bdf8')}>{c.username}@{c.host}:{c.port}</span>
                    <span style={S.badge(c.active ? '#34d399' : '#fb7185')}>{c.active ? '● ACTIVE' : '○ INACTIVE'}</span>
                  </div>
                </div>
                <div style={{ display:'flex', gap:8 }}>
                  <button style={S.btn('#38bdf8')} onClick={() => {
                    setCheckoutModal(c.id)
                    setCheckoutTask('')
                    setCheckoutResult(null)
                  }}>
                    <Key size={12}/> Checkout
                  </button>
                  {c.active && (
                    <button style={S.btn('#fb7185')} onClick={() => deactivate(c.id)}>
                      <Trash2 size={12}/> Deactivate
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        }
      </Section>

      {/* Policies */}
      <Section title="ACCESS POLICIES" icon={Shield} color="#34d399">
        <div style={{ display:'flex', justifyContent:'flex-end', marginBottom:16 }}>
          <button style={S.btn('#34d399')} onClick={() => setShowPolicyForm(!showPolicyForm)}><Plus size={12}/> Add Policy</button>
        </div>

        {showPolicyForm && (
          <div style={{ ...S.card, border:'1px solid #34d39930', marginBottom:16 }}>
            <div style={S.row}>
              <div style={S.col}><div style={S.label}>Policy ID</div><input style={S.input} placeholder="readonly-disk" value={policyForm.id} onChange={e=>setPolicyForm({...policyForm,id:e.target.value})} /></div>
              <div style={S.col}><div style={S.label}>Name</div><input style={S.input} placeholder="Read-only disk inspection" value={policyForm.name} onChange={e=>setPolicyForm({...policyForm,name:e.target.value})} /></div>
            </div>
            <div style={S.row}>
              <div style={S.col}>
                <div style={S.label}>Credential ID</div>
                <select style={{...S.input, cursor:'pointer'}} value={policyForm.credential_id} onChange={e=>setPolicyForm({...policyForm,credential_id:e.target.value})}>
                  <option value="">Select credential...</option>
                  {creds.map(c => <option key={c.id} value={c.id}>{c.id}</option>)}
                </select>
              </div>
              <div style={{flex:1}}><div style={S.label}>Max Minutes</div><input style={S.input} type="number" value={policyForm.max_session_minutes} onChange={e=>setPolicyForm({...policyForm,max_session_minutes:e.target.value})} /></div>
            </div>
            <div style={S.row}>
              <div style={S.col}><div style={S.label}>Allowed Commands (comma-sep)</div><input style={S.input} value={policyForm.allowed_commands} onChange={e=>setPolicyForm({...policyForm,allowed_commands:e.target.value})} /></div>
              <div style={S.col}><div style={S.label}>Denied Commands (comma-sep)</div><input style={S.input} value={policyForm.denied_commands} onChange={e=>setPolicyForm({...policyForm,denied_commands:e.target.value})} /></div>
            </div>
            <div style={{ display:'flex', gap:8, marginTop:8 }}>
              <button style={S.btn('#34d399')} onClick={submitPolicy}><CheckCircle size={12}/> Save</button>
              <button style={S.btn('#6b7280')} onClick={() => setShowPolicyForm(false)}><XCircle size={12}/> Cancel</button>
            </div>
          </div>
        )}

        {policies.length === 0 ? <div style={{ color:'#4a4a6a', fontSize:13 }}>No policies defined.</div> :
          policies.map(p => (
            <div key={p.id} style={S.card}>
              <div style={{ fontFamily:"'Space Mono',monospace", fontSize:13, color:'#34d399', marginBottom:4 }}>{p.id}</div>
              <div style={{ fontSize:12, color:'#6b7280', marginBottom:10 }}>{p.name} · credential: {p.credential_id} · {p.max_session_minutes}min max</div>
              <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
                {p.allowed_commands.map(c => <span key={c} style={S.badge('#34d399')}>{c}</span>)}
                {p.denied_commands.map(c => <span key={c} style={S.badge('#fb7185')}>✕ {c}</span>)}
              </div>
            </div>
          ))
        }
      </Section>

      {/* Manual Checkout Modal */}
      {checkoutModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
        }}>
          <div style={{ background: '#12121a', border: '1px solid #38bdf840', borderRadius: 10, padding: 28, width: 460 }}>
            <div style={{ fontFamily: "'Space Mono',monospace", fontSize: 14, color: '#38bdf8', marginBottom: 6 }}>
              MANUAL CHECKOUT
            </div>
            <div style={{ fontSize: 12, color: '#4a4a6a', marginBottom: 20 }}>
              Credential: <span style={{ color: '#e2e8f0' }}>{checkoutModal}</span>
            </div>

            {!checkoutResult ? (
              <>
                <div style={S.label}>Task Description</div>
                <input
                  style={{ ...S.input, marginBottom: 16 }}
                  placeholder="What do you need this access for?"
                  value={checkoutTask}
                  onChange={e => setCheckoutTask(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && submitCheckout()}
                  autoFocus
                />
                <div style={{ display: 'flex', gap: 8 }}>
                  <button style={S.btn('#38bdf8')} onClick={submitCheckout}>
                    <Key size={12}/> Issue Token
                  </button>
                  <button style={S.btn('#6b7280')} onClick={() => setCheckoutModal(null)}>
                    <XCircle size={12}/> Cancel
                  </button>
                </div>
              </>
            ) : (
              <>
                <div style={{ background: '#34d39910', border: '1px solid #34d39930', borderRadius: 6, padding: 14, marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: '#34d399', fontFamily: "'Space Mono',monospace", marginBottom: 12 }}>
                    ✓ TOKEN ISSUED
                  </div>
                  {[
                    ['Host',     `${checkoutResult.host}:${checkoutResult.port}`],
                    ['Username', checkoutResult.username],
                    ['Expires',  new Date(checkoutResult.expires_at).toLocaleTimeString()],
                    ['Allowed',  checkoutResult.allowed_commands?.join(', ')],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'flex-start' }}>
                      <span style={{ fontSize: 11, color: '#4a4a6a', fontFamily: "'Space Mono',monospace", width: 70, flexShrink: 0 }}>{k}</span>
                      <span style={{ fontSize: 11, color: '#e2e8f0' }}>{v}</span>
                    </div>
                  ))}
                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontSize: 11, color: '#4a4a6a', fontFamily: "'Space Mono',monospace", marginBottom: 6 }}>TOKEN</div>
                    <div style={{
                      fontSize: 10, color: '#38bdf8', fontFamily: "'Space Mono',monospace",
                      background: '#050508', padding: 10, borderRadius: 4,
                      wordBreak: 'break-all', lineHeight: 1.8, userSelect: 'all',
                    }}>
                      {checkoutResult.token}
                    </div>
                  </div>
                </div>
                <button style={S.btn('#6b7280')} onClick={() => setCheckoutModal(null)}>
                  <XCircle size={12}/> Close
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
