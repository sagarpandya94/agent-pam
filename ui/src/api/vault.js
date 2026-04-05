const BASE = 'http://localhost:8000'

export async function getCredentials() {
  const r = await fetch(`${BASE}/credentials/`)
  if (!r.ok) throw new Error('Failed to fetch credentials')
  return r.json()
}

export async function createCredential(data) {
  const r = await fetch(`${BASE}/credentials/`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function deactivateCredential(id) {
  await fetch(`${BASE}/credentials/${id}`, { method: 'DELETE' })
}

export async function getPolicies() {
  const r = await fetch(`${BASE}/policies/`)
  if (!r.ok) throw new Error('Failed to fetch policies')
  return r.json()
}

export async function createPolicy(data) {
  const r = await fetch(`${BASE}/policies/`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getSessions() {
  const r = await fetch(`${BASE}/checkout/sessions`)
  if (!r.ok) throw new Error('Failed to fetch sessions')
  return r.json()
}

export async function checkoutCredential(agentId, credentialId, taskDescription) {
  const r = await fetch(`${BASE}/checkout/`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      agent_id: agentId,
      credential_id: credentialId,
      task_description: taskDescription,
    })
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}