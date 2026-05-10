import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'OneAgent OS',
  description: 'Unified AI Agent System — 24 Frameworks in One Interface',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ar" dir="rtl">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body style={{ margin: 0, background: '#080810', color: '#E8E6F0' }}>{children}</body>
    </html>
  )
}
