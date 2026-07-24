import { useState } from 'react'
import { Card, Upload, Table, Tag, Progress, Descriptions, Collapse, Typography, Space, message } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'

const { Dragger } = Upload
const { Text } = Typography

interface FieldItem { field_name: string; value: unknown; confidence: number }
interface ParseResult {
  doc_type: string; doc_type_label: string; ocr_text: string
  ocr_confidence: number; fields: FieldItem[]; overall_confidence: number; processing_time_ms: number
}

const DOC_TYPES = [
  { type: 'waybill', label: '运单' }, { type: 'receipt', label: '回单' },
  { type: 'warehouse_doc', label: '仓储单' }, { type: 'invoice', label: '发票' }, { type: 'id_document', label: '证件' },
]

export default function DocumentParser() {
  const [result, setResult] = useState<ParseResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [fileList, setFileList] = useState<UploadFile[]>([])

  const handleUpload = async (file: File) => {
    setLoading(true)
    const form = new FormData()
    form.append('file', file)
    try {
      const r = await fetch('/api/v1/documents/parse', { method: 'POST', body: form })
      const body = await r.json()
      if (body.code !== 0) throw new Error(body.message)
      setResult(body.data)
      message.success('解析完成')
    } catch (e: any) { message.error(e.message) }
    finally { setLoading(false) }
    return false
  }

  return (
    <div style={{ maxWidth: 900, margin: '32px auto', padding: '0 16px' }}>
      <h2 style={{ marginBottom: 24 }}>多模态物流单据解析</h2>
      <Card style={{ marginBottom: 16 }}>
        <Dragger beforeUpload={(f) => { handleUpload(f); return false }} showUploadList={false}>
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">点击或拖拽单据影像到此处上传</p>
          <p className="ant-upload-hint">支持 JPG/PNG/TIFF/PDF，单文件最大 10MB</p>
        </Dragger>
      </Card>

      {loading && <Card><Progress percent={99} status="active" /><div style={{ textAlign: 'center' }}>解析中...</div></Card>}

      {result && (
        <Card title="解析结果">
          <Descriptions column={3} bordered size="small">
            <Descriptions.Item label="文档类型"><Tag color="blue">{result.doc_type_label}</Tag></Descriptions.Item>
            <Descriptions.Item label="OCR置信度">{(result.ocr_confidence * 100).toFixed(0)}%</Descriptions.Item>
            <Descriptions.Item label="综合置信度">
              <Progress percent={Math.round(result.overall_confidence * 100)} size="small" style={{ width: 120 }} />
            </Descriptions.Item>
            <Descriptions.Item label="处理耗时">{result.processing_time_ms}ms</Descriptions.Item>
          </Descriptions>

          <h4 style={{ marginTop: 16 }}>字段提取</h4>
          <Table dataSource={result.fields} rowKey="field_name" size="small" pagination={false}
            columns={[
              { title: '字段名', dataIndex: 'field_name' },
              { title: '值', dataIndex: 'value' },
              { title: '置信度', dataIndex: 'confidence', render: (v: number) => (
                <Tag color={v >= 0.9 ? 'green' : v >= 0.7 ? 'orange' : 'red'}>{(v * 100).toFixed(0)}%</Tag>
              )},
            ]}
          />

          <Collapse items={[{ key: '1', label: 'OCR 原始文本', children: <pre style={{ fontSize: 12, maxHeight: 200, overflow: 'auto' }}>{result.ocr_text}</pre> }]} style={{ marginTop: 16 }} />
        </Card>
      )}

      <Card title="支持的单据类型" size="small" style={{ marginTop: 16 }}>
        <Space wrap>{DOC_TYPES.map(d => <Tag key={d.type}>{d.label}</Tag>)}</Space>
      </Card>
    </div>
  )
}
