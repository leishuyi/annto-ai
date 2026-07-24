import { ReactNode, useState } from 'react'
import { Layout as AntLayout, Menu, Breadcrumb, Switch, Space, Avatar, Dropdown } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import { CustomerServiceOutlined, HomeOutlined, MoonOutlined, SunOutlined, UserOutlined, SettingOutlined, LogoutOutlined } from '@ant-design/icons'

const { Header, Content, Footer } = AntLayout

export default function Layout({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [dark, setDark] = useState(false)

  const pathParts = location.pathname.split('/').filter(Boolean)
  const selectedKey = pathParts.length >= 1 ? `/${pathParts[0]}` : '/'

  const breadcrumbs = [
    { title: <><HomeOutlined /> 首页</> },
  ]
  if (pathParts[0] === 'tickets') {
    breadcrumbs.push({ title: <><CustomerServiceOutlined /> 客服工单</> })
    if (pathParts[1]) breadcrumbs.push({ title: pathParts[2] === 'review' ? '人工授权' : `工单 #${pathParts[1]}` })
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px', background: 'linear-gradient(135deg, #1677ff 0%, #0958d9 100%)', boxShadow: '0 2px 8px rgba(0,0,0,0.15)', height: 56, position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ color: '#fff', fontSize: 18, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 10, marginRight: 48, cursor: 'pointer' }} onClick={() => navigate('/tickets')}>
          <CustomerServiceOutlined style={{ fontSize: 22 }} />
          annto·A2A 客服
        </div>
        <Menu theme="dark" mode="horizontal" selectedKeys={[selectedKey]}
          items={[{ key: '/tickets', icon: <CustomerServiceOutlined />, label: '客服工单' }]}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, minWidth: 0, borderBottom: 'none', background: 'transparent' }} />
        <Space>
          <Switch checked={dark} onChange={setDark} checkedChildren={<MoonOutlined />} unCheckedChildren={<SunOutlined />} />
          <Dropdown menu={{ items: [
            { key: 'profile', icon: <UserOutlined />, label: '个人信息' },
            { key: 'settings', icon: <SettingOutlined />, label: '系统设置' },
            { type: 'divider' },
            { key: 'logout', icon: <LogoutOutlined />, label: '退出', danger: true },
          ]}}>
            <Avatar size="small" icon={<UserOutlined />} style={{ background: '#87d068', cursor: 'pointer' }} />
          </Dropdown>
        </Space>
      </Header>
      <Content style={{ padding: '0 24px', marginTop: 12 }}>
        <Breadcrumb items={breadcrumbs} style={{ marginBottom: 12 }} />
        <div style={{ padding: 24, background: dark ? '#141414' : '#fff', borderRadius: 8, minHeight: 360 }}>
          {children}
        </div>
      </Content>
      <Footer style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>annto A2A 智能客服平台 ©2026</Footer>
    </AntLayout>
  )
}
