const BASE = 'http://localhost:8001'

export async function runTaskStream(task, credentialId, onChunk) {
  const r = await fetch(`${BASE}/agent/run`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, credential_id: credentialId })
  })
  if (!r.ok) throw new Error('Agent API error')
  const reader = r.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const text = decoder.decode(value)
    const lines = text.split('\n').filter(l => l.startsWith('data: '))
    for (const line of lines) {
      try { onChunk(JSON.parse(line.slice(6))) } catch {}
    }
  }
}

export async function getAuditEvents() {
  const r = await fetch(`${BASE}/agent/sessions`)
  if (!r.ok) throw new Error('Failed to fetch audit events')
  return r.json()
}

export async function getSessionEvents(token) {
  const r = await fetch(`${BASE}/agent/sessions/${encodeURIComponent(token)}`)
  if (!r.ok) throw new Error('Failed to fetch session events')
  return r.json()
}
