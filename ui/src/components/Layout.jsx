import { NavLink } from 'react-router-dom'
import { Shield, Terminal, ScrollText, Vault } from 'lucide-react'

const nav = [
  { to: '/',       icon: Vault,      label: 'Vault'  },
  { to: '/agent',  icon: Terminal,   label: 'Agent'  },
  { to: '/audit',  icon: ScrollText, label: 'Audit'  },
]

export default function Layout({ children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside style={{
        width: 220, background: '#0d0d14',
        borderRight: '1px solid #1e1e2e',
        display: 'flex', flexDirection: 'column',
        padding: '24px 0', position: 'fixed',
        top: 0, left: 0, bottom: 0, zIndex: 10
      }}>
        {/* Logo */}
        <div style={{ padding: '0 24px 32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Shield size={20} color="#fbbf24" />
            <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 14, color: '#fbbf24', letterSpacing: 2 }}>
              AGENT-PAM
            </span>
          </div>
          <div style={{ marginTop: 4, fontSize: 11, color: '#4a4a6a', fontFamily: "'Space Mono', monospace" }}>
            PAM FOR AI AGENTS
          </div>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1 }}>
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 24px', textDecoration: 'none',
                color: isActive ? '#fbbf24' : '#6b7280',
                background: isActive ? 'rgba(251,191,36,0.06)' : 'transparent',
                borderLeft: isActive ? '2px solid #fbbf24' : '2px solid transparent',
                fontSize: 13, fontWeight: 500, transition: 'all 0.15s',
              })}>
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid #1e1e2e' }}>
          <div style={{ fontSize: 10, color: '#2a2a3a', fontFamily: "'Space Mono', monospace" }}>
            NHI SECURITY v0.1.0
          </div>
        </div>
      </aside>

      {/* Main */}
      <main style={{ marginLeft: 220, flex: 1, padding: '32px 40px', minHeight: '100vh' }}>
        {children}
      </main>
    </div>
  )
}
