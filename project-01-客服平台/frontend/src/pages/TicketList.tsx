import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Modal, Form, Input, DatePicker, Select, InputNumber, Space, Tag, message } from 'antd'
import { PlusOutlined, PlayCircleOutlined, EyeOutlined } from '@ant-design/icons'
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
      message.success('工单创建成功')
      setModalOpen(false)
      form.resetFields()
      load()
    } catch (e: any) { message.error(e.message) }
    finally { setSubmitting(false) }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>客服工单</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>新建工单</Button>
      </div>
      <Table dataSource={tickets} rowKey="id" loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: load, showTotal: (t) => `共 ${t} 条` }}
        columns={[
          { title: '工单编号', dataIndex: 'case_no', width: 160 },
          { title: '客户', dataIndex: 'insured_name', width: 100 },
          { title: '运单号', dataIndex: 'order_no', width: 140 },
          { title: '发件人', dataIndex: 'sender', width: 120 },
          { title: '收件人', dataIndex: 'receiver', width: 120 },
          { title: '目的地', dataIndex: 'destination', width: 120, ellipsis: true },
          { title: '状态', dataIndex: 'status', width: 100, render: (s: string) => {
            const m = statusMap[s] ?? { color: 'default', text: s }
            return <Tag color={m.color}>{m.text}</Tag>
          }},
          { title: '创建时间', dataIndex: 'created_at', width: 170, render: (v: string) => new Date(v).toLocaleString('zh-CN') },
          { title: '操作', width: 160, render: (_: unknown, r: Ticket) => (
            <Space>
              <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/tickets/${r.id}`)}>详情</Button>
              {r.status === 'draft' && (
                <Button size="small" type="primary" icon={<PlayCircleOutlined />}
                  onClick={async () => { await api.runAgents(r.id); message.success('Agent链路已触发'); load() }}>
                  执行Agent
                </Button>
              )}
            </Space>
          )},
        ]}
      />
      <Modal title="新建客服工单" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={handleCreate} confirmLoading={submitting} width={640}>
        <Form form={form} layout="vertical">
          <Form.Item name="insured_name" label="客户名称" rules={[{ required: true }]}><Input placeholder="客户名称" /></Form.Item>
          <Form.Item name="order_no" label="运单号"><Input placeholder="如 ORD-202407001" /></Form.Item>
          <Form.Item name="sender" label="发件人"><Input /></Form.Item>
          <Form.Item name="receiver" label="收件人"><Input /></Form.Item>
          <Form.Item name="destination" label="目的地"><Input /></Form.Item>
          <Form.Item name="incident_desc" label="问题描述" rules={[{ required: true }]}><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="incident_date" label="日期" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="total_amount" label="货值(元)"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
