import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import TicketList from './pages/TicketList'
import TicketDetail from './pages/TicketDetail'
import HumanGate from './pages/HumanGate'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/tickets" element={<TicketList />} />
        <Route path="/tickets/:id" element={<TicketDetail />} />
        <Route path="/tickets/:id/review" element={<HumanGate />} />
        <Route path="*" element={<Navigate to="/tickets" replace />} />
      </Routes>
    </Layout>
  )
}
