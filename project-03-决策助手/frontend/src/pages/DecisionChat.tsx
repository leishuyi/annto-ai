import { useState, useRef, useEffect } from 'react'
import {
  Card, Input, Button, Space, Tag, Typography, Spin, Segmented,
  Collapse, Table, Progress, Empty, Tooltip, Avatar, Badge
} from 'antd'
import {
  SendOutlined, RobotOutlined, UserOutlined, BulbOutlined,
  ThunderboltOutlined, DatabaseOutlined, ExperimentOutlined,
  StopOutlined, ReloadOutlined, CopyOutlined
} from '@ant-design/icons'

const { TextArea } = Input
const { Text, Title } = Typography

const SUGGESTIONS = [
  { text: '华东区空调库存多少？', icon: <DatabaseOutlined />, mode: 'reasoning' },
  { text: '最近一周销售趋势', icon: <BulbOutlined />, mode: 'nl2sql' },
  { text: '如果销量增长30%会怎样？', icon: <ExperimentOutlined />, mode: 'simulation' },
  { text: '上周配送准时率？', icon: <ThunderboltOutlined />, mode: 'nl2sql' },
]

type Mode = 'reasoning' | 'nl2sql' | 'simulation'

const MODE_CONFIG: Record<Mode, { label: string; icon: JSX.Element; color: string; desc: string }> = {
  reasoning: { label: '决策推理', icon: <ThunderboltOutlined />, color: '#1677ff', desc: '多Agent协同分析，给出推荐方案' },
  nl2sql: { label: '数据查询', icon: <DatabaseOutlined />, color: '#52c41a', desc: '自然语言转SQL，查询供应链数据' },
  simulation: { label: '仿真推演', icon: <ExperimentOutlined />, color: '#722ed1', desc: '假设场景模拟，评估供应链影响' },
}

export default function DecisionChat() {
  const [messages, setMessages] = useState<{ role: string; content: any; mode?: Mode; id: string }[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<Mode>('reasoning')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (text: string) => {
    if (!text.trim() || loading) return
    setMessages(prev => [...prev, { role: 'user', content: text, id: `u-${Date.now()}` }])
    setInput('')
    setLoading(true)
    try {
      const endpoint = mode === 'nl2sql' ? '/api/v1/decision/nl2sql'
        : mode === 'simulation' ? '/api/v1/decision/simulate' : '/api/v1/decision/ask'
      const r = await fetch(endpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const body = await r.json()
      setMessages(prev => [...prev, { role: 'assistant', content: body.data || body, mode, id: `a-${Date.now()}` }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: { error: '请求失败，请重试' }, mode, id: `a-${Date.now()}` }])
    }
    setLoading(false)
  }

  const renderContent = (msg: { role: string; content: any; mode?: Mode }) => {
    if (msg.role === 'user') return <Text style={{ fontSize: 15, lineHeight: 1.6, color: msg.role === 'user' ? '#fff' : undefined }}>{msg.content as string}</Text>
    const d = msg.content as Record<string, any>
    if (d?.error) return <Text type="danger">{d.error}</Text>
    if (!d || Object.keys(d).length === 0) return <Text type="secondary">无数据返回</Text>
    return (
      <div>
        {d.recommendation && (
          <Card size="small" style={{ marginBottom: 12, background: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 8 }}>
            <Space><BulbOutlined style={{ color: '#52c41a' }} /><Text strong>建议</Text></Space>
            <div style={{ marginTop: 8 }}><Text>{d.recommendation}</Text></div>
          </Card>
        )}
        {d.impact && (
          <Card size="small" style={{ marginBottom: 12, borderRadius: 8 }}>
            <Text>{d.impact}</Text>
            {d.confidence && <div style={{ marginTop: 8 }}><Text type="secondary" style={{ fontSize: 12 }}>置信度 </Text><Progress percent={Math.round(d.confidence * 100)} size="small" style={{ width: 120 }} /></div>}
          </Card>
        )}
        {d.data?.stock?.results && (
          <Card size="small" title="库存数据" style={{ marginBottom: 12, borderRadius: 8 }}>
            <Table size="small" pagination={false} dataSource={d.data.stock.results} rowKey="warehouse_id"
              columns={[{ title: '仓库', dataIndex: 'warehouse_id', width: 120 }, { title: 'SKU', dataIndex: 'sku', width: 100 }, { title: '产品', dataIndex: 'product' }, { title: '库存', dataIndex: 'qty', width: 80, render: (v: number) => <Text strong>{v}</Text> }]} />
          </Card>
        )}
        {d.data?.forecast && (
          <Card size="small" title="预测" style={{ marginBottom: 12, borderRadius: 8 }}>
            <Space><StatCard label="日均销量" value={d.data.forecast.avg_daily} /><StatCard label="7日预测" value={d.data.forecast.predicted_7day} /><StatCard label="置信度" value={`${Math.round(d.data.forecast.confidence * 100)}%`} /></Space>
          </Card>
        )}
        {d.results?.length > 0 && (
          <Table size="small" pagination={false} dataSource={d.results} rowKey={(_, i) => String(i)}
            columns={Object.keys(d.results[0] || {}).slice(0, 4).map(k => ({ title: k, dataIndex: k, render: (v: any) => typeof v === 'number' ? <Text strong>{v.toLocaleString()}</Text> : String(v) }))} />
        )}
        {d.sql && <Collapse items={[{ key: '1', label: <Space><DatabaseOutlined />SQL 查询</Space>, children: <pre style={{ fontSize: 12, background: '#1f1f1f', color: '#fff', padding: 12, borderRadius: 6 }}>{d.sql}</pre> }]} style={{ marginBottom: 8 }} />}
        {d.reasoning_steps && <Space wrap style={{ marginTop: 8 }}>{d.reasoning_steps.map((s: string, i: number) => <Tag key={s} color="blue">Step{i+1}:{s}</Tag>)}</Space>}
        {d.scenario && <Tag color="purple">场景:{d.scenario}</Tag>}
        {d.chart_type && <Tag color="geekblue">图表:{d.chart_type}</Tag>}
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', height: '100vh', display: 'flex', flexDirection: 'column', background: '#f5f5f5' }}>
      <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0', background: '#fff' }}>
        <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Avatar icon={<RobotOutlined />} style={{ background: '#1677ff' }} />
            <div><Title level={4} style={{ margin: 0 }}>供应链智能决策助手</Title><Text type="secondary" style={{ fontSize: 12 }}>{MODE_CONFIG[mode].desc}</Text></div>
          </Space>
          <Segmented value={mode} onChange={v => setMode(v as Mode)}
            options={['reasoning', 'nl2sql', 'simulation'].map(k => {
              const m = k as Mode
              return { value: m, label: <Space>{MODE_CONFIG[m].icon}{MODE_CONFIG[m].label}</Space> }
            })} />
        </Space>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '16px 24px' }}>
        {messages.length === 0 ? (
          <div style={{ marginTop: 80 }}>
            <Empty image={<RobotOutlined style={{ fontSize: 64, color: '#1677ff' }} />}
              description={<div><Title level={5} style={{ color: '#666', marginBottom: 20 }}>输入供应链问题开始分析</Title><Space wrap style={{ justifyContent: 'center' }}>{SUGGESTIONS.map(s => (
                <Badge key={s.text} count={<Tag style={{ margin: 0, fontSize: 11 }}>{s.mode}</Tag>} offset={[-8, 8]}>
                  <Button size="large" icon={s.icon} onClick={() => send(s.text)} style={{ borderRadius: 20, height: 40 }}>{s.text}</Button>
                </Badge>
              ))}</Space></div>} />
          </div>
        ) : messages.map((m) => (
          <div key={m.id} className="fade-in" style={{ marginBottom: 16, display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{ maxWidth: '75%' }}>
              <Space style={{ marginBottom: 4, padding: '0 4px' }}>
                {m.role === 'assistant' && <Avatar size={28} icon={<RobotOutlined />} style={{ background: '#1677ff' }} />}
                <Text strong style={{ fontSize: 13 }}>{m.role === 'user' ? '我' : 'AI助手'}</Text>
                {m.mode && <Tag style={{ fontSize: 11 }}>{MODE_CONFIG[m.mode]?.label || m.mode}</Tag>}
              </Space>
              <Card size="small" style={{ borderRadius: 12, background: m.role === 'user' ? '#1677ff' : '#fff', border: m.role === 'user' ? 'none' : '1px solid #f0f0f0' }}>
                {renderContent(m)}
              </Card>
            </div>
          </div>
        ))}
        {loading && <div className="fade-in" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 4px' }}><Spin size="small" /><Text type="secondary">AI 正在思考...</Text></div>}
        <div ref={bottomRef} />
      </div>
      <div style={{ padding: '12px 24px 20px', borderTop: '1px solid #f0f0f0', background: '#fff' }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea value={input} onChange={e => setInput(e.target.value)}
            onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); send(input) } }}
            placeholder={`输入${MODE_CONFIG[mode].label}问题...`} rows={2} style={{ borderRadius: 8, fontSize: 14, flex: 1 }} disabled={loading} />
          <Tooltip title="发送 (Enter)">
            <Button type="primary" icon={loading ? <StopOutlined /> : <SendOutlined />}
              onClick={() => loading ? setLoading(false) : send(input)}
              style={{ height: 52, width: 56, borderRadius: 8 }} danger={loading} />
          </Tooltip>
        </Space.Compact>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: any }) {
  return (
    <div style={{ textAlign: 'center', padding: '8px 16px', background: '#fafafa', borderRadius: 8, minWidth: 100 }}>
      <div style={{ fontSize: 12, color: '#999' }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: '#1677ff' }}>{value}</div>
    </div>
  )
}
