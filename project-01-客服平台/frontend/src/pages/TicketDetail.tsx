import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Space, Spin, Divider } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import AgentTraceView from '../components/AgentTrace'
import type { Ticket, AgentTrace } from '../types'

const statusMap: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '待处理' }, processing: { color: 'processing', text: '处理中' },
  agents_completed: { color: 'blue', text: 'Agent完成' }, pending_review: { color: 'orange', text: '待审核' },
  approved: { color: 'green', text: '已通过' }, rejected: { color: 'red', text: '已驳回' },
}

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [traces, setTraces] = useState<AgentTrace[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([api.getTicket(Number(id)), api.getTraces(Number(id))])
      .then(([c, t]) => { setTicket(c); setTraces(t) })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!ticket) return <div>工单不存在</div>

  const summaryTrace = traces.find(t => t.agent_name === 'agent_summary')

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tickets')}>返回列表</Button>
      </Space>
      <Card title={<Space><span>{ticket.case_no}</span><Tag>{statusMap[ticket.status]?.text}</Tag></Space>}>
        <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="客户">{ticket.insured_name}</Descriptions.Item>
          <Descriptions.Item label="运单号">{ticket.order_no || '-'}</Descriptions.Item>
          <Descriptions.Item label="发件人">{ticket.sender || '-'}</Descriptions.Item>
          <Descriptions.Item label="收件人">{ticket.receiver || '-'}</Descriptions.Item>
          <Descriptions.Item label="目的地">{ticket.destination || '-'}</Descriptions.Item>
          <Descriptions.Item label="货值">{ticket.total_amount ? `¥${ticket.total_amount}` : '-'}</Descriptions.Item>
          <Descriptions.Item label="问题描述" span={3}>{ticket.incident_desc}</Descriptions.Item>
        </Descriptions>
      </Card>
      <Divider />
      <AgentTraceView traces={traces} loading={false} />
      {ticket.status === 'pending_review' && (
        <>
          <Divider />
          <div style={{ textAlign: 'center' }}>
            <Button type="primary" size="large" icon={<CheckCircleOutlined />}
              onClick={() => navigate(`/tickets/${ticket.id}/review`)}>进入人工授权</Button>
          </div>
        </>
      )}
    </div>
  )
}
