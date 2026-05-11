import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Jnus — Think Once. Do Everything.',
  description: 'مساعد ذكاء اصطناعي يفهم هدفك، يبني خطة تنفيذ تلقائية، ويستخدم أنسب أداة لكل مهمة — بدون أي إعداد منك.',
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
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Noto+Kufi+Arabic:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body style={{ margin: 0, background: '#F5F3EF', color: '#1A1814' }}>{children}</body>
    </html>
  )
}
