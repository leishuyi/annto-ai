import { useState } from 'react'
import {
  Card, Upload, Table, Tag, Progress, Descriptions, Collapse,
  Typography, Space, Button, Row, Col, Statistic, Divider, Steps, Alert, Empty
} from 'antd'
import {
  InboxOutlined, FileTextOutlined, CheckCircleOutlined,
  CloseCircleOutlined, ClockCircleOutlined, ExperimentOutlined,
  UploadOutlined, WarningOutlined
} from '@ant-design/icons'

const { Dragger } = Upload
const { Text, Title } = Typography

interface FieldItem { field_name: string; value: unknown; confidence: number }
interface ParseResult {
  doc_type: string; doc_type_label: string; ocr_text: string
  ocr_confidence: number; fields: FieldItem[]; overall_confidence: number; processing_time_ms: number
}

const DOC_TYPES = [
  { type: 'waybill', label: '运单', icon: '📦', color: '#1677ff', fields: '运单号、收发件人、重量' },
  { type: 'receipt', label: '回单', icon: '📋', color: '#52c41a', fields: '签收人、日期、货物状态' },
  { type: 'warehouse_doc', label: '仓储单', icon: '🏭', color: '#722ed1', fields: 'SKU、数量、库位' },
  { type: 'invoice', label: '发票', icon: '🧾', color: '#faad14', fields: '发票号、金额、日期' },
  { type: 'id_document', label: '证件', icon: '🆔', color: '#eb2f96', fields: '姓名、证件号' },
]

function getConfidenceColor(conf: number): string {
  return conf >= 0.9 ? '#52c41a' : conf >= 0.7 ? '#faad14' : '#ff4d4f'
}

function getConfidenceLabel(conf: number): string {
  return conf >= 0.95 ? '高' : conf >= 0.8 ? '中' : '低'
}

/** 根据置信度给出下一步操作建议 */
function getNextAction(conf: number): string {
  if (conf >= 0.95) return '可自动处理，无需人工干预'
  if (conf >= 0.8) return '建议人工快速抽检确认'
  return '置信度偏低，需人工重新录入'
}

export default function DocumentParser() {
  const [result, setResult] = useState<ParseResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<ParseResult[]>([])
  const [step, setStep] = useState<'upload' | 'parsing' | 'done'>('upload')

  const handleUpload = async (file: File) => {
    setLoading(true)
    setStep('parsing')
    const form = new FormData()
    form.append('file', file)
    try {
      const r = await fetch('/api/v1/documents/parse', { method: 'POST', body: form })
      const body = await r.json()
      if (body.code !== 0) throw new Error(body.message)
      setResult(body.data)
      setHistory(prev => [body.data, ...prev].slice(0, 10))
      setStep('done')
    } catch (e: any) {
      // error shown by message
    } finally { setLoading(false) }
    return false
  }

  return (
    <div className="page-container">
      <Title level={3} style={{ marginBottom: 4 }}>多模态物流单据解析</Title>
      <Text type="secondary" style={{ fontSize: 14, display: 'block', marginBottom: 24 }}>
        上传物流单据影像（拍照/扫描/PDF），AI 自动识别类型并提取结构化字段
      </Text>

      {/* 流程指引 */}
      <Steps current={step === 'upload' ? 0 : step === 'parsing' ? 1 : 2} size="small" style={{ marginBottom: 24, maxWidth: 500 }}>
        <Steps.Step title="上传单据" description="支持 JPG/PNG/PDF" icon={<UploadOutlined />} />
        <Steps.Step title="AI 解析" description="分类+OCR+提取" icon={<FileTextOutlined />} />
        <Steps.Step title="获取结果" description="结构化数据" icon={<CheckCircleOutlined />} />
      </Steps>

      {/* 上传区域 */}
      <Card style={{ marginBottom: 24, borderRadius: 12 }} className="hover-card">
        <Dragger
          beforeUpload={(f) => { handleUpload(f); return false }}
          showUploadList={false}
          style={{ borderRadius: 12 }}
          disabled={loading}
        >
          <p style={{ fontSize: 48, margin: 0, color: '#1677ff' }}>
            <InboxOutlined />
          </p>
          <p style={{ fontSize: 16, fontWeight: 600, margin: '12px 0 4px' }}>
            {loading ? '正在解析...' : '点击或拖拽单据影像到此处上传'}
          </p>
          <p style={{ color: '#999', fontSize: 13 }}>
            支持 JPG / PNG / TIFF / PDF，单文件最大 10MB
          </p>
        </Dragger>
      </Card>

      {/* 解析中状态 */}
      {loading && (
        <Card style={{ marginBottom: 24, textAlign: 'center', borderRadius: 12 }}>
          <Progress type="circle" percent={99} status="active" width={80} />
          <div style={{ marginTop: 12, color: '#666' }}>
            <ClockCircleOutlined style={{ marginRight: 6 }} />
            正在解析单据...（OCR识别 → 文档分类 → 字段提取 → 置信度校准）
          </div>
        </Card>
      )}

      {/* 解析结果 */}
      {result && !loading && (
        <>
          {/* 置信度预警 */}
          {result.overall_confidence < 0.8 && (
            <Alert
              type="warning"
              showIcon
              icon={<WarningOutlined />}
              message="置信度偏低，建议人工复核"
              description={`综合置信度 ${(result.overall_confidence * 100).toFixed(0)}%，${getNextAction(result.overall_confidence)}`}
              style={{ marginBottom: 16, borderRadius: 8 }}
            />
          )}

          <Card
            className="slide-up"
            style={{ marginBottom: 24, borderRadius: 12, border: `2px solid ${getConfidenceColor(result.overall_confidence)}` }}
            title={
              <Space>
                <FileTextOutlined style={{ color: '#1677ff' }} />
                <span>解析结果</span>
                <Tag color={getConfidenceColor(result.overall_confidence)}>
                  综合 {(result.overall_confidence * 100).toFixed(0)}%
                </Tag>
                <Tag style={{ fontSize: 11 }}>
                  {getNextAction(result.overall_confidence)}
                </Tag>
              </Space>
            }
          >
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <div className="metric-card" style={{ background: '#f0f5ff' }}>
                  <div className="metric-value" style={{ color: '#1677ff', fontSize: 20 }}>{result.doc_type_label}</div>
                  <div className="metric-label">文档类型</div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card" style={{ background: '#f6ffed' }}>
                  <div className="metric-value" style={{ color: '#52c41a', fontSize: 24 }}>{(result.ocr_confidence * 100).toFixed(0)}%</div>
                  <div className="metric-label">OCR 置信度</div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card" style={{ background: '#fff7e6' }}>
                  <div className="metric-value" style={{ color: '#faad14', fontSize: 24 }}>{result.fields.length}</div>
                  <div className="metric-label">提取字段数</div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card" style={{ background: '#fff0f0' }}>
                  <div className="metric-value" style={{ color: '#ff4d4f', fontSize: 20 }}>{result.processing_time_ms}ms</div>
                  <div className="metric-label">处理耗时</div>
                </div>
              </Col>
            </Row>

            {/* 下一步操作建议 */}
            <Alert
              type={result.overall_confidence >= 0.9 ? 'success' : result.overall_confidence >= 0.7 ? 'warning' : 'error'}
              showIcon
              message="处理建议"
              description={getNextAction(result.overall_confidence)}
              style={{ marginBottom: 16, borderRadius: 8 }}
            />

            {/* 置信度指示器 */}
            <div style={{ marginBottom: 16, padding: '12px 16px', background: '#fafafa', borderRadius: 8 }}>
              <Space align="center" style={{ width: '100%' }}>
                <Text strong>综合置信度</Text>
                <Progress percent={Math.round(result.overall_confidence * 100)} strokeColor={getConfidenceColor(result.overall_confidence)} style={{ flex: 1, margin: '0 16px' }} />
                <Tag color={getConfidenceColor(result.overall_confidence)}>{getConfidenceLabel(result.overall_confidence)}</Tag>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {result.overall_confidence >= 0.95 ? '自动处理 ✓' : result.overall_confidence >= 0.8 ? '建议抽检' : '需人工录入'}
                </Text>
              </Space>
            </div>

            <Divider style={{ margin: '12px 0' }} />

            <Title level={5} style={{ marginBottom: 12 }}>字段提取结果</Title>
            <Table dataSource={result.fields} rowKey="field_name" size="middle" pagination={false} style={{ marginBottom: 16 }}
              columns={[
                { title: '字段名', dataIndex: 'field_name', width: 120, render: (v: string) => <Text strong>{v}</Text> },
                { title: '提取值', dataIndex: 'value', width: 200 },
                { title: '置信度', dataIndex: 'confidence', width: 120, render: (v: number) => (
                  <Space>
                    <Progress percent={Math.round(v * 100)} size="small" strokeColor={getConfidenceColor(v)} style={{ width: 80 }} />
                    <Text style={{ color: getConfidenceColor(v), fontSize: 12 }}>{(v * 100).toFixed(0)}%</Text>
                  </Space>
                )},
                { title: '评估', key: 'eval', width: 100, render: (_: unknown, record: FieldItem) => (
                  record.confidence >= 0.9 ? <Tag icon={<CheckCircleOutlined />} color="success">可信</Tag>
                    : record.confidence >= 0.7 ? <Tag icon={<CloseCircleOutlined />} color="warning">存疑</Tag>
                    : <Tag icon={<CloseCircleOutlined />} color="error">需复核</Tag>
                )},
              ]}
            />

            {/* OCR 原文 */}
            <Collapse items={[{
              key: '1',
              label: <Space><ExperimentOutlined />OCR 原始文本（仅供参考）</Space>,
              children: <pre style={{ fontSize: 13, maxHeight: 200, overflow: 'auto', background: '#f5f5f5', padding: 12, borderRadius: 6, margin: 0 }}>{result.ocr_text}</pre>
            }]} />
          </Card>
        </>
      )}

      {/* 支持的单据类型 */}
      <Card title="📄 支持的单据类型（点击可查看示例字段）" style={{ borderRadius: 12 }} size="small">
        <Row gutter={[16, 12]}>
          {DOC_TYPES.map(dt => (
            <Col span={8} key={dt.type}>
              <Card size="small" className="hover-card" style={{ borderRadius: 8, borderLeft: `3px solid ${dt.color}` }}>
                <Space>
                  <span style={{ fontSize: 24 }}>{dt.icon}</span>
                  <div>
                    <div style={{ fontWeight: 600 }}>{dt.label}</div>
                    <Text type="secondary" style={{ fontSize: 12 }}>{dt.fields}</Text>
                  </div>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 解析历史 */}
      {history.length > 1 && (
        <Card title="📋 解析历史" size="small" style={{ marginTop: 16, borderRadius: 12 }}>
          {history.slice(1).map((h, i) => (
            <Button key={i} type="text" style={{ display: 'block', width: '100%', textAlign: 'left', marginBottom: 4 }}
              onClick={() => { setResult(h); setStep('done') }}>
              <Space>
                <Tag color="blue">{h.doc_type_label}</Tag>
                <Text>综合 {(h.overall_confidence * 100).toFixed(0)}%</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>{h.processing_time_ms}ms</Text>
              </Space>
            </Button>
          ))}
        </Card>
      )}
    </div>
  )
}
