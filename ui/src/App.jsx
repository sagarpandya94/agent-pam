import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import VaultPage from './pages/Vault'
import AgentPage from './pages/Agent'
import AuditPage from './pages/Audit'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"      element={<VaultPage />} />
          <Route path="/agent" element={<AgentPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
