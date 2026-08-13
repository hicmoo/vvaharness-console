import { NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Scans from './pages/Scans'
import ScanDetailPage from './pages/ScanDetail'
import Findings from './pages/Findings'
import Targets from './pages/Targets'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          vvaharness <span>console</span>
        </div>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/scans">Scans</NavLink>
          <NavLink to="/findings">Findings</NavLink>
          <NavLink to="/targets">Targets</NavLink>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scans" element={<Scans />} />
          <Route path="/scans/:id" element={<ScanDetailPage />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
