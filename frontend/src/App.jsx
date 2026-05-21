import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Reports from './pages/Reports'
import { getCargoFromToken } from './services/api'

function AdminRoute({ children }) {
  if (!localStorage.getItem('token')) return <Navigate to="/login" replace />
  if (getCargoFromToken() !== 'admin') {
    localStorage.removeItem('token')
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<AdminRoute><Dashboard /></AdminRoute>} />
      <Route path="/reports" element={<AdminRoute><Reports /></AdminRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
