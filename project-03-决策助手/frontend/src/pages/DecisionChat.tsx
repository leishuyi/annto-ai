import { useState, useRef, useEffect } from 'react'
import { Card, Input, Button, Space, Tag, Typography, Spin, Segmented, Collapse, Table, Progress, Empty } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined, BulbOutlined } from '@ant-design/icons'

const { TextArea } = Input
const { Text, Title } = Typography

const SUGGESTIONS = [
  '华东区空调库存多少？', '上周配送准时率怎么样？',
  '如果销量增长30%会怎样？', '华东区库存情况',
]

type Mode = 'reasoning' | 'nl2sql' | 'simulation'

export default function DecisionChat() {
  const [messages, setMessages] = useState<{ role: string; content: any; mode?: Mode }[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<Mode>('reasoning')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (text: string) => {
    if (!text.trim()) return
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    try {
      const endpoint = mode === 'nl2sql' ? '/api/v1/decision/nl2sql'
        : mode === 'simulation' ? '/api/v1/decision/simulate'
        : '/api/v1/decision/ask'
      const body = mode === 'simulation'
        ? JSON.stringify({ text, params: {} })
        : JSON.stringify({ text })
      const r = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
      const data = await r.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.data || data, mode }])
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: { error: e.message } }])
    }
    setLoading(false)
  }

  const renderContent = (msg: { role: string; content: any; mode?: Mode }) => {
    if (msg.role === 'user') return <Text>{msg.content as string}</Text>
    const d = msg.content as Record<string, any>
    if (!d || d.error) return <Text type="danger">{d?.error || '无响应'}</Text>

    return (
      <div>
        {d.recommendation && <Card size="small" style={{ marginBottom: 8, background: '#f6ffed' }}><Text strong>{d.recommendation}</Text></Card>}
        {d.impact && <Card size="small" style={{ marginBottom: 8 }}><Text>{d.impact}</Text><br /><Text type="secondary">置信度: <Progress percent={Math.round((d.confidence || 0) * 100)} size="small" style={{ width: 100 }} /></Text></Card>}
        {d.data?.stock?.results && (
          <Table size="small" pagination={false} dataSource={d.data.stock.results} rowKey="warehouse_id"
            columns={[{ title: '仓库', dataIndex: 'warehouse_id' }, { title: 'SKU', dataIndex: 'sku' }, { title: '产品', dataIndex: 'product' }, { title: '库存', dataIndex: 'qty' }]} />
        )}
        {d.data?.forecast && <Tag>A日均销量: {d.data.forecast.avg_daily}</Tag>}
        {d.results && Array.isArray(d.results) && (
          <Table size="small" pagination={false} dataSource={d.results} rowKey={(_, i) => String(i)}
            columns={Object.keys(d.results[0] || {}).map(k => ({ title: k, dataIndex: k }))} />
        )}
        {d.sql && <Collapse items={[{ key: '1', label: 'SQL', children: <pre style={{ fontSize: 12 }}>{d.sql}</pre> }]} />}
        {d.reasoning_steps && <Space wrap style={{ marginTop: 8 }}>{d.reasoning_steps.map((s: string) => <Tag key={s} color="blue">{s}</Tag>)}</Space>}
        {d.scenario && <Text>场景: {d.scenario}</Text>}
        {d.chart_type && <Tag>图表类型: {d.chart_type}</Tag>}
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 16, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}><RobotOutlined /> 供应链智能决策助手</Title>
        <Segmented options={[
          { value: 'reasoning', label: '决策推理' },
          { value: 'nl2sql', label: '数据查询' },
          { value: 'simulation', label: '仿真推演' },
        ]} value={mode} onChange={v => setMode(v as Mode)} />
      </div>

      <div style={{ flex: 1, overflow: 'auto', marginBottom: 16 }}>
        {messages.length === 0 && (
          <Empty description={
            <div>
              <p style={{ marginBottom: 16 }}>输入问题或选择一个示例：</p>
              <Space wrap>
                {SUGGESTIONS.map(s => (
                  <Button key={s} size="small" icon={<BulbOutlined />} onClick={() => send(s)}>{s}</Button>
                ))}
              </Space>
            </div>
          } />
        )}
        {messages.map((m, i) => (
          <Card key={i} size="small" style={{ marginBottom: 8, background: m.role === 'user' ? '#f0f5ff' : '#fff' }}>
            <Space style={{ marginBottom: 8 }}>
              {m.role === 'user' ? <UserOutlined /> : <RobotOutlined style={{ color: '#1677ff' }} />}
              <Text strong>{m.role === 'user' ? '我' : 'AI助手'}</Text>
              {m.mode && <Tag>{m.mode}</Tag>}
            </Space>
            {renderContent(m)}
          </Card>
        ))}
        {loading && <Card><Spin tip="思考中..." /></Card>}
        <div ref={bottomRef} />
      </div>

      <Space.Compact style={{ width: '100%' }}>
        <TextArea value={input} onChange={e => setInput(e.target.value)}
          onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); send(input) }}}
          placeholder="输入供应链问题..." rows={2} style={{ flex: 1 }} />
        <Button type="primary" icon={<SendOutlined />} onClick={() => send(input)} loading={loading}
          style={{ height: 52 }}>发送</Button>
      </Space.Compact>
    </div>
  )
}
