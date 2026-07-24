import { ReactNode } from 'react'
import { Layout as AntLayout, Menu, theme } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import { CustomerServiceOutlined, ProfileOutlined } from '@ant-design/icons'

const { Header, Content, Footer } = AntLayout

export default function Layout({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()

  const pathParts = location.pathname.split('/').filter(Boolean)
  const selectedKey = pathParts.length >= 1 ? `/${pathParts[0]}` : '/'

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ color: '#fff', fontSize: 18, fontWeight: 700, marginRight: 48, cursor: 'pointer', letterSpacing: 1 }}
          onClick={() => navigate('/tickets')}>
          <CustomerServiceOutlined style={{ marginRight: 10, fontSize: 20 }} />
          annto·A2A 客服
        </div>
        <Menu theme="dark" mode="horizontal" selectedKeys={[selectedKey]}
          items={[{ key: '/tickets', icon: <ProfileOutlined />, label: '客服工单' }]}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, minWidth: 0, borderBottom: 'none' }} />
      </Header>
      <Content style={{ padding: '0 24px', marginTop: 16 }}>
        <div style={{ padding: 24, background: token.colorBgContainer, borderRadius: token.borderRadiusLG, minHeight: 360 }}>
          {children}
        </div>
      </Content>
      <Footer style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>
        annto A2A 智能客服平台 ©2026
      </Footer>
    </AntLayout>
  )
}
