import { useState } from 'react'
import { Tabs, Card, Input, Button, Descriptions, Tag, Table, Space, message, Typography, Row, Col, Statistic, Progress, Divider } from 'antd'
import { CarOutlined, SettingOutlined, EnvironmentOutlined, CheckCircleOutlined, MessageOutlined, WarningOutlined, DollarOutlined, ScheduleOutlined, BellOutlined } from '@ant-design/icons'

const { TextArea } = Input
const { Text, Title } = Typography

interface ApiResult { data?: any; code?: number; message?: string }

async function post(url: string, body: any): Promise<any> {
  try {
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    const d = await r.json()
    return d.data || d
  } catch (e: any) { message.error(e.message); return null }
}

export default function FieldAssistant() {
  const [origin, setOrigin] = useState('佛山'); const [dest, setDest] = useState('上海')
  const [customerName, setCustomerName] = useState(''); const [query, setQuery] = useState('')
  const [voiceText, setVoiceText] = useState(''); const [period, setPeriod] = useState('2026-07'); const [region, setRegion] = useState('华东')
  const [navResult, setNavResult] = useState<any>(null); const [signoffResult, setSignoffResult] = useState<any>(null)
  const [scriptResult, setScriptResult] = useState<any>(null); const [reportResult, setReportResult] = useState<any>(null)
  const [reconResult, setReconResult] = useState<any>(null); const [analysis, setAnalysis] = useState<any>(null)
  const [scheduleResult, setScheduleResult] = useState<any>(null); const [alerts, setAlerts] = useState<any>(null)
  const [rootCause, setRootCause] = useState<any>(null); const [loading, setLoading] = useState<string | null>(null)

  const call = async (key: string, url: string, body: any) => {
    setLoading(key); const r = await post(url, body); setLoading(null)
    if (r) {
      const setters: Record<string, (v: any) => void> = {
        nav: setNavResult, signoff: setSignoffResult, script: setScriptResult,
        report: setReportResult, recon: setReconResult, analysis: setAnalysis,
        schedule: setScheduleResult, alerts: setAlerts, root: setRootCause,
      }
      setters[key]?.(r)
    }
  }

  const driverCards = [
    { key: 'nav', title: '导航规划', icon: <EnvironmentOutlined />, color: '#1677ff', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="出发点" value={origin} onChange={e => setOrigin(e.target.value)} />
        <Input placeholder="目的地" value={dest} onChange={e => setDest(e.target.value)} />
        <Button type="primary" icon={<CarOutlined />} onClick={() => call('nav', '/api/v1/driver/navigate', { origin, destination: dest, vehicle_type: '轻卡' })} loading={loading === 'nav'}>规划路线</Button>
        {navResult && (
          <Card size="small" style={{ borderRadius: 8, background: '#f0f5ff' }}>
            <Row gutter={16}>
              <Col span={8}><Statistic title="总里程" value={navResult.total_km} suffix="km" valueStyle={{ color: '#1677ff' }} /></Col>
              <Col span={8}><Statistic title="预计时间" value={Math.round(navResult.estimated_min / 60)} suffix="h" /></Col>
              <Col span={8}><Statistic title="交通延迟" value={navResult.traffic_delay_min} suffix="min" valueStyle={{ color: navResult.traffic_delay_min > 0 ? '#faad14' : undefined }} /></Col>
            </Row>
            {navResult.waypoints && <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>{navResult.waypoints.map((w: any) => w.name).join(' → ')}</div>}
          </Card>
        )}
      </Space>
    )},
    { key: 'signoff', title: '签收核验', icon: <CheckCircleOutlined />, color: '#52c41a', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="客户名称" value={customerName} onChange={e => setCustomerName(e.target.value)} />
        <Button type="primary" style={{ background: '#52c41a' }} onClick={() => call('signoff', '/api/v1/driver/signoff', { customer_name: customerName })} loading={loading === 'signoff'}>核验签收</Button>
        {signoffResult && <Descriptions column={2} size="small" bordered>
          <Descriptions.Item label="签名"><Tag color={signoffResult.signature_match ? 'success' : 'error'}>{signoffResult.signature_match ? '匹配' : '不匹配'}</Tag></Descriptions.Item>
          <Descriptions.Item label="公章"><Tag color={signoffResult.seal_present ? 'success' : 'error'}>{signoffResult.seal_present ? '有' : '无'}</Tag></Descriptions.Item>
          <Descriptions.Item label="破损"><Tag color={!signoffResult.damage_detected ? 'success' : 'error'}>{signoffResult.damage_detected ? '有' : '无'}</Tag></Descriptions.Item>
          <Descriptions.Item label="置信度"><Progress percent={Math.round(signoffResult.confidence * 100)} size="small" style={{ width: 100 }} /></Descriptions.Item>
        </Descriptions>}
      </Space>
    )},
    { key: 'script', title: '话术助手', icon: <MessageOutlined />, color: '#722ed1', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <TextArea placeholder="客户说的话..." value={query} onChange={e => setQuery(e.target.value)} rows={3} />
        <Button type="primary" style={{ background: '#722ed1' }} onClick={() => call('script', '/api/v1/driver/script', { customer_query: query })} loading={loading === 'script'}>生成话术</Button>
        {scriptResult && (
          <div>
            <div style={{ marginBottom: 8 }}><Tag color={scriptResult.sentiment === 'negative' ? 'error' : scriptResult.sentiment === 'positive' ? 'success' : 'default'}>{scriptResult.sentiment === 'negative' ? '消极' : scriptResult.sentiment === 'positive' ? '积极' : '中性'}</Tag></div>
            <Card size="small" style={{ background: '#f6ffed', borderRadius: 8 }}><Text>{scriptResult.suggested_response}</Text></Card>
          </div>
        )}
      </Space>
    )},
    { key: 'report', title: '异常上报', icon: <WarningOutlined />, color: '#ff4d4f', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <TextArea placeholder="语音输入或输入异常描述..." value={voiceText} onChange={e => setVoiceText(e.target.value)} rows={3} />
        <Button type="primary" danger onClick={() => call('report', '/api/v1/driver/report', { voice_text: voiceText, location: origin })} loading={loading === 'report'}>提交上报</Button>
        {reportResult && (
          <Descriptions column={2} size="small" bordered>
            <Descriptions.Item label="类型"><Tag>{reportResult.issue_type}</Tag></Descriptions.Item>
            <Descriptions.Item label="优先级"><Tag color={reportResult.priority === 'high' ? 'red' : reportResult.priority === 'medium' ? 'orange' : 'blue'}>{reportResult.priority === 'high' ? '高' : reportResult.priority === 'medium' ? '中' : '低'}</Tag></Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>{reportResult.description}</Descriptions.Item>
          </Descriptions>
        )}
      </Space>
    )},
  ]

  const opsCards = [
    { key: 'recon', title: '财务对账', icon: <DollarOutlined />, color: '#1677ff', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="对账周期" value={period} onChange={e => setPeriod(e.target.value)} style={{ width: 200 }} />
        <Space>
          <Button icon={<DollarOutlined />} onClick={() => call('recon', '/api/v1/ops/reconcile', { period })} loading={loading === 'recon'}>执行对账</Button>
          <Button onClick={() => call('analysis', '/api/v1/ops/reconcile/analyze', { period })} loading={loading === 'analysis'}>差异分析</Button>
        </Space>
        {reconResult && <Row gutter={16}>
          <Col span={6}><Card size="small"><Statistic title="总发票" value={reconResult.total_invoices} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="匹配" value={reconResult.matched_count} valueStyle={{ color: '#52c41a' }} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="差异" value={reconResult.unmatched_count} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="总金额" value={reconResult.total_amount} prefix="¥" precision={0} /></Card></Col>
        </Row>}
        {analysis && <Card size="small" style={{ background: '#fff7e6', borderRadius: 8 }}><Text>{analysis.discrepancy_reason}</Text></Card>}
      </Space>
    )},
    { key: 'schedule', title: '智能排班', icon: <ScheduleOutlined />, color: '#52c41a', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="区域" value={region} onChange={e => setRegion(e.target.value)} style={{ width: 200 }} />
        <Button icon={<ScheduleOutlined />} onClick={() => call('schedule', '/api/v1/ops/schedule', { region, date: '2026-07-25' })} loading={loading === 'schedule'}>生成排班</Button>
        {scheduleResult?.assignments && (
          <div>
            <Text>共 {scheduleResult.total_drivers} 名司机，{scheduleResult.total_orders} 单</Text>
            <Table size="small" pagination={false} dataSource={scheduleResult.assignments} rowKey="driver"
              columns={[{ title: '司机', dataIndex: 'driver' }, { title: '订单数', dataIndex: 'orders' }, { title: '区域', dataIndex: 'region' }, { title: '车型', dataIndex: 'vehicle' }]} />
          </div>
        )}
      </Space>
    )},
    { key: 'alerts', title: '异常看板', icon: <BellOutlined />, color: '#ff4d4f', content: (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Button icon={<BellOutlined />} onClick={() => call('alerts', '/api/v1/ops/alerts', {})} loading={loading === 'alerts'}>刷新预警</Button>
        {alerts?.alerts && <Table size="small" pagination={false} dataSource={alerts.alerts} rowKey="id"
          columns={[
            { title: '类型', dataIndex: 'type', render: (v: string) => <Tag>{v}</Tag> },
            { title: '级别', dataIndex: 'level', render: (v: string) => <Tag color={v === 'critical' ? 'red' : v === 'warning' ? 'orange' : 'blue'}>{v === 'critical' ? '严重' : v === 'warning' ? '警告' : '信息'}</Tag> },
            { title: '消息', dataIndex: 'message', ellipsis: true },
            { title: '时间', dataIndex: 'time', width: 160 },
            { title: '操作', width: 100, render: (_: any, r: any) => <Button size="small" onClick={async () => { const result = await post(`/api/v1/ops/alerts/${r.id}/root-cause`, {}); if (result) setRootCause(result) }}>根因分析</Button> },
          ]} />}
        {rootCause && <Card title="根因分析" size="small" style={{ borderRadius: 8 }}><Text>{rootCause.root_cause}</Text><Divider /><Text type="secondary">建议：{rootCause.recommendation}</Text></Card>}
      </Space>
    )},
  ]

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <Title level={3} style={{ marginBottom: 24 }}>一线人员智能助手</Title>
      <Tabs defaultActiveKey="driver" items={[
        { key: 'driver', label: <span><CarOutlined /> 司机端</span>, children: (
          <Row gutter={[16, 16]}>
            {driverCards.map(c => <Col span={12} key={c.key}>
              <Card title={<Space><span style={{ color: c.color, fontSize: 20 }}>{c.icon}</span><span>{c.title}</span></Space>}
                style={{ borderRadius: 12, height: '100%' }} className="hover-card">{c.content}</Card>
            </Col>)}
          </Row>
        )},
        { key: 'ops', label: <span><SettingOutlined /> 运营端</span>, children: (
          <Row gutter={[16, 16]}>
            {opsCards.map(c => <Col span={24} key={c.key}>
              <Card title={<Space><span style={{ color: c.color, fontSize: 20 }}>{c.icon}</span><span>{c.title}</span></Space>}
                style={{ borderRadius: 12 }} className="hover-card">{c.content}</Card>
            </Col>)}
          </Row>
        )},
      ]} />
    </div>
  )
}
