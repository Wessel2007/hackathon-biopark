import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Reports from './pages/Reports'
import ReportsLogin from './pages/ReportsLogin'
import { getCargoFromToken } from './services/api'

function PrivateRoute({ children }) {
  return localStorage.getItem('token') ? children : <Navigate to="/login" replace />
}

function AdminRoute({ children }) {
  if (!localStorage.getItem('token')) return <Navigate to="/login" replace />
  if (getCargoFromToken() !== 'admin') return <Navigate to="/" replace />
  return children
}

function PrivateReportsRoute({ children }) {
  if (!localStorage.getItem('token')) return <Navigate to="/login" replace />
  if (!localStorage.getItem('reports_token')) return <Navigate to="/reports-login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/reports-login" element={<AdminRoute><ReportsLogin /></AdminRoute>} />
      <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/reports" element={<PrivateReportsRoute><Reports /></PrivateReportsRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
