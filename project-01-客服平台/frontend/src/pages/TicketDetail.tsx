import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Space, Spin, Divider, Steps, Result, message } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, PlayCircleOutlined, ClockCircleOutlined, RobotOutlined, FileTextOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import AgentTraceView from '../components/AgentTrace'
import type { Ticket, AgentTrace } from '../types'

const statusMap: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '待处理' }, processing: { color: 'processing', text: '处理中' },
  agents_completed: { color: 'blue', text: 'Agent完成' }, pending_review: { color: 'orange', text: '待审核' },
  approved: { color: 'green', text: '已通过' }, rejected: { color: 'red', text: '已驳回' },
}

/** 每个状态的当前步骤（0-indexed）和后续引导 */
const STATUS_STEP: Record<string, { current: number; hint: string }> = {
  draft: { current: 0, hint: '工单已创建，点击下方按钮启动 Agent 智能处理链路。6 个 Agent 将依次执行：订单查询→单据录入→财务对账→调度校验→风控检测→结论汇总。' },
  processing: { current: 0, hint: 'Agent 正在执行中，请稍候... Trace 面板会实时更新每个 Agent 的执行状态。' },
  agents_completed: { current: 1, hint: '所有 Agent 已完成分析，正在等待人工授权。请查看 Agent 的处理结论。' },
  pending_review: { current: 1, hint: '请进入人工授权页面审核 Agent 的结论。支持通过、驳回或修改金额后通过。' },
  approved: { current: 2, hint: '已审核通过，流程已完成。' },
  rejected: { current: 2, hint: '已驳回。如需重新处理，请联系管理员。' },
}

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [traces, setTraces] = useState<AgentTrace[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  const load = () => {
    if (!id) return
    setLoading(true)
    Promise.all([api.getTicket(Number(id)), api.getTraces(Number(id))])
      .then(([c, t]) => { setTicket(c); setTraces(t) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!ticket) return <Result status="error" title="工单不存在" extra={<Button onClick={() => navigate('/tickets')}>返回列表</Button>} />

  const st = STATUS_STEP[ticket.status] || STATUS_STEP.draft
  const summaryTrace = traces.find(t => t.agent_name === 'agent_summary')

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tickets')}>返回列表</Button>
      </Space>

      {/* 流程进度条 */}
      <Card size="small" style={{ marginBottom: 16, borderRadius: 8 }}>
        <Steps current={st.current} size="small"
          items={[
            { title: '工单创建', description: '客户信息录入', icon: <FileTextOutlined /> },
            { title: 'Agent 处理', description: '6 Agent 链路分析', icon: <RobotOutlined />,
              status: ticket.status === 'draft' ? 'wait' : ticket.status === 'processing' ? 'process' : 'finish' },
            { title: '人工授权', description: '审核并确认结论', icon: <SafetyCertificateOutlined />,
              status: ticket.status === 'approved' || ticket.status === 'rejected' ? 'finish' : ticket.status === 'pending_review' ? 'process' : 'wait' },
          ]}
        />
        <div style={{ marginTop: 8, padding: '8px 12px', background: '#f6f8fa', borderRadius: 6, fontSize: 13, color: '#666' }}>
          <ClockCircleOutlined style={{ marginRight: 6 }} />
          {st.hint}
        </div>
      </Card>

      {/* 工单信息卡片 */}
      <Card title={<Space><span>工单 {ticket.case_no}</span><Tag>{statusMap[ticket.status]?.text}</Tag></Space>}>
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

      {/* Agent 执行追溯 */}
      <AgentTraceView traces={traces} loading={false} />

      {/* 下一步操作 */}
      <Divider />
      <div style={{ textAlign: 'center', padding: '16px 0' }}>
        {ticket.status === 'draft' && (
          <Space direction="vertical" size={12}>
            <div style={{ color: '#666', fontSize: 13 }}>启动 Agent 智能处理链路，6 个 Agent 将依次分析此工单</div>
            <Button type="primary" size="large" icon={<PlayCircleOutlined />}
              loading={running}
              onClick={async () => {
                setRunning(true)
                try {
                  await api.runAgents(Number(id))
                  message.success('Agent 链路已触发！处理完成后将进入审核环节。')
                  load()
                } catch (e: any) { message.error(e.message) }
                setRunning(false)
              }}>
              执行 Agent 链路
            </Button>
          </Space>
        )}
        {ticket.status === 'pending_review' && (
          <Space direction="vertical" size={12}>
            <div style={{ color: '#666', fontSize: 13 }}>Agent 已完成所有分析，请审核结论并执行人工授权</div>
            <Button type="primary" size="large" icon={<CheckCircleOutlined />}
              onClick={() => navigate(`/tickets/${ticket.id}/review`)}>
              进入人工授权
            </Button>
          </Space>
        )}
        {(ticket.status === 'approved') && (
          <Result status="success" title="已审核通过" subTitle={`理算金额: ¥${ticket.calculated_amount?.toLocaleString() || '-'}`} />
        )}
        {(ticket.status === 'rejected') && (
          <Result status="error" title="已驳回" subTitle="请联系相关人员处理" />
        )}
      </div>
    </div>
  )
}
