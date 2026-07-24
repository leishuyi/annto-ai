import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Modal, Form, Input, DatePicker, Select, InputNumber, Space, Tag, message, Steps, Empty, Card, Result } from 'antd'
import { PlusOutlined, PlayCircleOutlined, EyeOutlined, FileTextOutlined, RobotOutlined, CheckCircleOutlined, CustomerServiceOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import type { Ticket } from '../types'

const statusMap: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '待处理' },
  processing: { color: 'processing', text: '处理中' },
  agents_completed: { color: 'blue', text: 'Agent完成' },
  pending_review: { color: 'orange', text: '待审核' },
  approved: { color: 'green', text: '已通过' },
  rejected: { color: 'red', text: '已驳回' },
}

/** 工单流转步骤：当前状态 → 下一步操作 */
const WORKFLOW_STEPS: Record<string, { step: number; hint: string; action: string }> = {
  draft: { step: 0, hint: '新建工单后，点击"执行Agent"启动智能处理', action: '执行Agent' },
  processing: { step: 1, hint: 'Agent正在分析处理中，请稍候...', action: '等待完成' },
  agents_completed: { step: 2, hint: '所有Agent已完成，等待人工审核', action: '查看详情' },
  pending_review: { step: 2, hint: '请进入人工授权页面处理', action: '前往审核' },
  approved: { step: 3, hint: '已审核通过，流程结束', action: '查看详情' },
  rejected: { step: 3, hint: '已驳回，如有疑问可重新提交', action: '查看详情' },
}

export default function TicketList() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  const load = async (p = 1) => {
    setLoading(true)
    try {
      const data = await api.getTickets({ page: p, page_size: 20 })
      setTickets(data.items)
      setTotal(data.total)
      setPage(data.page)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    const v = await form.validateFields()
    setSubmitting(true)
    try {
      await api.createTicket({
        insured_name: v.insured_name,
        insurance_product: v.insurance_product || '物流运输',
        incident_desc: v.incident_desc,
        incident_date: v.incident_date.format('YYYY-MM-DD'),
        total_amount: v.total_amount,
        order_no: v.order_no,
        sender: v.sender,
        receiver: v.receiver,
        destination: v.destination,
      })
      message.success('工单创建成功！接下来请点击"执行Agent"启动智能处理流程。')
      setModalOpen(false)
      form.resetFields()
      load()
    } catch (e: any) { message.error(e.message) }
    finally { setSubmitting(false) }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20 }}>客服工单</h2>
          <div style={{ color: '#999', fontSize: 13, marginTop: 4 }}>管理客服工单，追踪 Agent 智能处理进度</div>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} size="large">新建工单</Button>
      </div>

      {/* 流程指引卡片 — 仅列表为空时展示 */}
      {tickets.length === 0 && !loading && (
        <Card style={{ marginBottom: 24, borderRadius: 12 }}>
          <Result
            icon={<CustomerServiceOutlined style={{ color: '#1677ff' }} />}
            title="开始使用智能客服平台"
            subTitle="三步完成工单智能处理：创建工单 → 启动Agent链路 → 人工授权"
            extra={
              <Steps current={-1} direction="horizontal" style={{ maxWidth: 600, margin: '0 auto' }}
                items={[
                  { title: '创建工单', description: '填写客户信息和问题描述', icon: <FileTextOutlined /> },
                  { title: 'Agent 处理', description: '6个AI Agent自动分析处理', icon: <RobotOutlined /> },
                  { title: '人工授权', description: '审核Agent结论并确认', icon: <CheckCircleOutlined /> },
                ]}
              />
            }
          />
        </Card>
      )}

      <Table dataSource={tickets} rowKey="id" loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: load, showTotal: (t) => `共 ${t} 条` }}
        columns={[
          { title: '工单编号', dataIndex: 'case_no', width: 160 },
          { title: '客户', dataIndex: 'insured_name', width: 100 },
          { title: '运单号', dataIndex: 'order_no', width: 140, render: (v: string) => v || <span style={{ color: '#ccc' }}>待录入</span> },
          { title: '发件人', dataIndex: 'sender', width: 120 },
          { title: '收件人', dataIndex: 'receiver', width: 120 },
          { title: '目的地', dataIndex: 'destination', width: 120, ellipsis: true },
          { title: '状态', dataIndex: 'status', width: 100, render: (s: string) => {
            const m = statusMap[s] ?? { color: 'default', text: s }
            return <Tag color={m.color}>{m.text}</Tag>
          }},
          { title: '创建时间', dataIndex: 'created_at', width: 170, render: (v: string) => new Date(v).toLocaleString('zh-CN') },
          { title: '操作', width: 200, render: (_: unknown, r: Ticket) => {
            const wf = WORKFLOW_STEPS[r.status] || WORKFLOW_STEPS.draft
            return (
              <Space>
                <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/tickets/${r.id}`)}>详情</Button>
                {r.status === 'draft' && (
                  <Button size="small" type="primary" icon={<PlayCircleOutlined />}
                    onClick={async () => {
                      await api.runAgents(r.id)
                      message.success('Agent 链路已触发！请稍候查看处理结果。')
                      load()
                    }}>
                    执行Agent
                  </Button>
                )}
                {r.status === 'pending_review' && (
                  <Button size="small" type="primary" style={{ background: '#faad14', borderColor: '#faad14' }}
                    icon={<CheckCircleOutlined />}
                    onClick={() => navigate(`/tickets/${r.id}/review`)}>
                    去审核
                  </Button>
                )}
              </Space>
            )
          }},
        ]}
        // 空状态：无工单时的引导
        locale={{
          emptyText: (
            <Empty description={
              <span>
                还没有工单<br />
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} style={{ marginTop: 12 }}>
                  创建第一个工单
                </Button>
              </span>
            } />
          )
        }}
      />

      <Modal title="新建客服工单" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={handleCreate} confirmLoading={submitting} width={640}
        okText="创建工单" cancelText="取消">
        <Form form={form} layout="vertical">
          <Form.Item name="insured_name" label="客户名称" rules={[{ required: true, message: '请输入客户名称' }]}>
            <Input placeholder="如：上海华联超市" />
          </Form.Item>
          <Form.Item name="order_no" label="运单号" tooltip="物流运单编号，如 ORD-202407001">
            <Input placeholder="ORD-202407001" />
          </Form.Item>
          <Form.Item name="sender" label="发件人"><Input placeholder="如：佛山美的工业园" /></Form.Item>
          <Form.Item name="receiver" label="收件人"><Input placeholder="如：张经理" /></Form.Item>
          <Form.Item name="destination" label="目的地"><Input placeholder="如：上海市浦东新区" /></Form.Item>
          <Form.Item name="incident_desc" label="问题描述" rules={[{ required: true, message: '请描述问题' }]}>
            <Input.TextArea rows={3} placeholder="请描述客户遇到的问题，Agent 将据此进行分析..." />
          </Form.Item>
          <Form.Item name="incident_date" label="日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} placeholder="选择发生日期" />
          </Form.Item>
          <Form.Item name="total_amount" label="货值(元)" tooltip="货物总价值，用于AI分析和风控评估">
            <InputNumber style={{ width: '100%' }} min={0} placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
