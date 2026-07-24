import { useState } from 'react'
import { Tabs, Card, Input, Button, Descriptions, Tag, Table, Space, message, Typography, Spin } from 'antd'
import { CarOutlined, SettingOutlined } from '@ant-design/icons'

const { TextArea } = Input
const { Text } = Typography

export default function FieldAssistant() {
  const [navResult, setNavResult] = useState<any>(null)
  const [signoffResult, setSignoffResult] = useState<any>(null)
  const [scriptResult, setScriptResult] = useState<any>(null)
  const [reportResult, setReportResult] = useState<any>(null)
  const [reconResult, setReconResult] = useState<any>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [scheduleResult, setScheduleResult] = useState<any>(null)
  const [alerts, setAlerts] = useState<any>(null)
  const [rootCause, setRootCause] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const [origin, setOrigin] = useState('佛山')
  const [dest, setDest] = useState('上海')
  const [customerName, setCustomerName] = useState('')
  const [query, setQuery] = useState('')
  const [voiceText, setVoiceText] = useState('')
  const [period, setPeriod] = useState('2026-07')
  const [region, setRegion] = useState('华东')

  const post = async (url: string, body: any) => {
    setLoading(true)
    try {
      const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      const d = await r.json()
      return d.data || d
    } catch (e: any) { message.error(e.message) }
    finally { setLoading(false) }
    return null
  }

  const driverTabs = [
    { key: 'nav', label: '导航规划', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="出发点" value={origin} onChange={e => setOrigin(e.target.value)} />
        <Input placeholder="目的地" value={dest} onChange={e => setDest(e.target.value)} />
        <Button onClick={async () => {
          const r = await post('/api/v1/driver/navigate', { origin, destination: dest, vehicle_type: '轻卡' })
          if (r) setNavResult(r)
        }}>规划路线</Button>
        {navResult && <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="总里程">{navResult.total_km}km</Descriptions.Item>
          <Descriptions.Item label="预计时间">{navResult.estimated_min}min</Descriptions.Item>
          <Descriptions.Item label="交通延迟">{navResult.traffic_delay_min}min</Descriptions.Item>
          <Descriptions.Item label="途经点" span={2}>{navResult.waypoints?.map((w: any) => w.name).join(' → ')}</Descriptions.Item>
        </Descriptions>}
      </Space>
    )},
    { key: 'signoff', label: '签收核验', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="客户名称" value={customerName} onChange={e => setCustomerName(e.target.value)} />
        <Button onClick={async () => {
          const r = await post('/api/v1/driver/signoff', { customer_name: customerName })
          if (r) setSignoffResult(r)
        }}>核验签收</Button>
        {signoffResult && <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="签名匹配"><Tag color={signoffResult.signature_match ? 'green' : 'red'}>{signoffResult.signature_match ? '匹配' : '不匹配'}</Tag></Descriptions.Item>
          <Descriptions.Item label="公章检测"><Tag color={signoffResult.seal_present ? 'green' : 'red'}>{signoffResult.seal_present ? '有' : '无'}</Tag></Descriptions.Item>
          <Descriptions.Item label="破损检测"><Tag color={!signoffResult.damage_detected ? 'green' : 'red'}>{signoffResult.damage_detected ? '有' : '无'}</Tag></Descriptions.Item>
        </Descriptions>}
      </Space>
    )},
    { key: 'script', label: '话术助手', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <TextArea placeholder="客户说的话..." value={query} onChange={e => setQuery(e.target.value)} rows={3} />
        <Button onClick={async () => {
          const r = await post('/api/v1/driver/script', { customer_query: query })
          if (r) setScriptResult(r)
        }}>生成话术</Button>
        {scriptResult && <Card size="small" style={{ background: '#f6ffed' }}>{scriptResult.suggested_response}</Card>}
      </Space>
    )},
    { key: 'report', label: '异常上报', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <TextArea placeholder="语音输入或输入异常描述..." value={voiceText} onChange={e => setVoiceText(e.target.value)} rows={3} />
        <Button onClick={async () => {
          const r = await post('/api/v1/driver/report', { voice_text: voiceText, location: origin })
          if (r) setReportResult(r)
        }}>提交上报</Button>
        {reportResult && <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="问题类型"><Tag>{reportResult.issue_type}</Tag></Descriptions.Item>
          <Descriptions.Item label="优先级"><Tag color={reportResult.priority === 'high' ? 'red' : 'orange'}>{reportResult.priority}</Tag></Descriptions.Item>
          <Descriptions.Item label="描述">{reportResult.description}</Descriptions.Item>
        </Descriptions>}
      </Space>
    )},
  ]

  const opsTabs = [
    { key: 'recon', label: '财务对账', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="对账周期" value={period} onChange={e => setPeriod(e.target.value)} />
        <Space>
          <Button onClick={async () => {
            const r = await post('/api/v1/ops/reconcile', { period })
            if (r) setReconResult(r)
          }}>执行对账</Button>
          <Button onClick={async () => {
            const r = await post('/api/v1/ops/reconcile/analyze', { period })
            if (r) setAnalysis(r)
          }}>差异分析</Button>
        </Space>
        {reconResult && <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="总发票">{reconResult.total_invoices}</Descriptions.Item>
          <Descriptions.Item label="匹配">{reconResult.matched_count}</Descriptions.Item>
          <Descriptions.Item label="差异"><Tag color="red">{reconResult.unmatched_count}</Tag></Descriptions.Item>
        </Descriptions>}
        {analysis && <Card size="small"><Text>{analysis.discrepancy_reason}</Text></Card>}
      </Space>
    )},
    { key: 'schedule', label: '智能排班', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="区域" value={region} onChange={e => setRegion(e.target.value)} />
        <Button onClick={async () => {
          const r = await post('/api/v1/ops/schedule', { region, date: '2026-07-25' })
          if (r) setScheduleResult(r)
        }}>生成排班</Button>
        {scheduleResult?.assignments && <Table size="small" pagination={false} dataSource={scheduleResult.assignments} rowKey="driver"
          columns={[{ title: '司机', dataIndex: 'driver' }, { title: '订单数', dataIndex: 'orders' }, { title: '区域', dataIndex: 'region' }, { title: '车型', dataIndex: 'vehicle' }]} />}
      </Space>
    )},
    { key: 'alerts', label: '异常看板', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Button onClick={async () => {
          const r = await post('/api/v1/ops/alerts', {})
          if (r) setAlerts(r)
        }} loading={loading}>刷新预警</Button>
        {alerts?.alerts && <Table size="small" pagination={false} dataSource={alerts.alerts} rowKey="id"
          columns={[
            { title: '类型', dataIndex: 'type' },
            { title: '级别', dataIndex: 'level', render: (v: string) => <Tag color={v === 'critical' ? 'red' : v === 'warning' ? 'orange' : 'blue'}>{v}</Tag> },
            { title: '消息', dataIndex: 'message' },
            { title: '时间', dataIndex: 'time' },
            { title: '操作', render: (_: any, r: any) => <Button size="small" onClick={async () => {
              const result = await post(`/api/v1/ops/alerts/${r.id}/root-cause`, {})
              if (result) setRootCause(result)
            }}>根因分析</Button> },
          ]} />}
        {rootCause && <Card title="根因分析" size="small"><Text>{rootCause.root_cause}</Text><br /><Text type="secondary">{rootCause.recommendation}</Text></Card>}
      </Space>
    )},
  ]

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 16 }}>
      <h2 style={{ marginBottom: 16 }}>一线人员智能助手</h2>
      <Tabs items={[
        { key: 'driver', label: <span><CarOutlined /> 司机端</span>, children: <Tabs items={driverTabs.map(t => ({ ...t, children: <Card key={t.key} title={t.label} size="small">{t.content}</Card> }))} /> },
        { key: 'ops', label: <span><SettingOutlined /> 运营端</span>, children: <Tabs items={opsTabs.map(t => ({ ...t, children: <Card key={t.key} title={t.label} size="small">{t.content}</Card> }))} /> },
      ]} />
    </div>
  )
}
