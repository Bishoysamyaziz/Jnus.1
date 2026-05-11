'use client'

import { useState, useEffect, useRef } from 'react'

// ── Color Palette ──────────────────────────────────────────────────
const C = {
  ink:     '#09090F',
  ink2:    '#0D0D16',
  paper:   '#F5F3EF',
  gold:    '#C9A84C',
  gold2:   '#E8CC80',
  golddim: '#C9A84C18',
  stone:   '#6B6860',
  stone2:  '#9C9888',
  line:    '#E2DDD6',
  line2:   '#2A2820',
  txt:     '#1A1814',
  muted:   '#6B6860',
  dim:     '#C8C4BC',
  green:   '#3D9970',
  red:     '#C0392B',
}

// ── Capabilities Data ──────────────────────────────────────────────
const CAPS = [
  { i:'⚡', h:'تنفيذ متوازٍ', d:'المهام المستقلة تنفذ في نفس الوقت مع تعافٍ تلقائي من الأخطاء.' },
  { i:'🧠', h:'فهم ذكي', d:'يحدد نوع طلبك تلقائياً بدقة عالية ويختار أنسب أسلوب للتنفيذ.' },
  { i:'💾', h:'ذاكرة دائمة', d:'يتذكر كل محادثة وكل قرار — ذاكرة سريعة + تاريخ دائم + بحث دلالي.' },
  { i:'🔀', h:'توجيه ذكي', d:'نموذج مجاني للبسيط، نموذج متقدم للمعقد. التكلفة دائماً أقل من سنت.' },
  { i:'🛡️', h:'تنفيذ آمن', d:'تنفيذ الكود في بيئة معزولة تماماً — بدون شبكة وبموارد محدودة.' },
  { i:'📊', h:'شفافية كاملة', d:'كل خطوة مسجلة — وقت التنفيذ، التكلفة، الأداة المستخدمة.' },
]

// ── Utility ────────────────────────────────────────────────────────
function uid() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

function esc(t: string) {
  return t.replace(/&/g, '&').replace(/</g, '<').replace(/>/g, '>')
}

function render(txt: string) {
  const lines = txt.split('\n')
  let out = '', inCode = false, codeBuf = '', lang = ''
  for (const l of lines) {
    if (l.startsWith('```')) {
      if (!inCode) { inCode = true; lang = l.slice(3); codeBuf = '' }
      else {
        out += `<div style="border-radius:8px;overflow:hidden;border:1px solid #1A1A2E;margin:8px 0">
          ${lang ? `<div style="padding:4px 12px;background:#111118;border-bottom:1px solid #1A1A2E;
            font-size:9px;color:#6B6860;font-family:'DM Mono',monospace;display:flex;justify-content:space-between">
            <span>${lang}</span><span style="color:${C.green}">● live</span></div>` : ''}
          <pre style="margin:0;border:none;border-radius:0">${esc(codeBuf)}</pre></div>`
        inCode = false; codeBuf = ''; lang = ''
      }
    } else if (inCode) { codeBuf += l + '\n' }
    else if (l === '') { out += '<div style="height:5px"></div>' }
    else {
      const s = l.replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--txt)">$1</strong>')
      out += `<span style="display:block;font-size:13px;line-height:1.85;color:var(--txt)">${s}</span>`
    }
  }
  return out
}

// ── Components ─────────────────────────────────────────────────────

function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 30)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav style={{
      position: 'fixed', top: 0, insetInline: 0, zIndex: 500,
      padding: '20px 48px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      transition: 'all .4s',
      borderBottom: scrolled ? `1px solid ${C.line}` : '1px solid transparent',
      background: scrolled ? 'rgba(245,243,239,.92)' : 'transparent',
      backdropFilter: scrolled ? 'blur(16px)' : 'none',
    }}>
      <a href="#" className="n-logo" style={{
        fontFamily: "'Playfair Display', serif", fontSize: 22, fontWeight: 900,
        color: C.ink, textDecoration: 'none', letterSpacing: -0.5,
      }} onClick={e => { e.preventDefault(); window.location.reload() }}>
        J<em style={{ color: C.gold, fontStyle: 'normal' }}>nus</em>
      </a>
      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        <a href="#how" style={{
          fontSize: 11, color: C.muted, textDecoration: 'none',
          fontFamily: "'DM Mono', monospace", letterSpacing: .5, transition: 'color .2s',
        }} onMouseEnter={e => e.currentTarget.style.color = C.txt}
           onMouseLeave={e => e.currentTarget.style.color = C.muted}>
          كيف يعمل
        </a>
        <a href="#capabilities" style={{
          fontSize: 11, color: C.muted, textDecoration: 'none',
          fontFamily: "'DM Mono', monospace", letterSpacing: .5, transition: 'color .2s',
        }} onMouseEnter={e => e.currentTarget.style.color = C.txt}
           onMouseLeave={e => e.currentTarget.style.color = C.muted}>
          القدرات
        </a>
        <a href="/chat" style={{
          padding: '8px 20px', background: C.ink, color: C.paper,
          borderRadius: 8, fontSize: 11, textDecoration: 'none',
          fontFamily: "'DM Mono', monospace", letterSpacing: .8, transition: 'all .2s',
        }} onMouseEnter={e => { e.currentTarget.style.background = C.gold; e.currentTarget.style.color = C.ink }}
           onMouseLeave={e => { e.currentTarget.style.background = C.ink; e.currentTarget.style.color = C.paper }}>
          ابدأ الآن
        </a>
      </div>
    </nav>
  )
}

function Hero() {
  return (
    <section style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', textAlign: 'center',
      padding: '140px 24px 80px', position: 'relative', overflow: 'hidden',
    }}>
      {/* Diagonal grid */}
      <div style={{
        content: '""', position: 'absolute', inset: '-50%',
        backgroundImage: `repeating-linear-gradient(45deg,transparent,transparent 48px,${C.line} 48px,${C.line} 49px),
          repeating-linear-gradient(-45deg,transparent,transparent 48px,${C.line} 48px,${C.line} 49px)`,
        opacity: .35, pointerEvents: 'none',
      }} />

      {/* Gold halo */}
      <div style={{
        position: 'absolute', width: 600, height: 600, borderRadius: '50%',
        background: `radial-gradient(circle,${C.golddim} 0%,transparent 70%)`,
        top: '50%', left: '50%', transform: 'translate(-50%,-55%)', pointerEvents: 'none',
      }} />

      {/* Eyebrow */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 10,
        padding: '6px 16px', border: `1px solid ${C.gold}`, borderRadius: 20,
        background: C.golddim, fontSize: 10, color: C.gold,
        fontFamily: "'DM Mono', monospace", letterSpacing: 1.5, marginBottom: 32,
        position: 'relative', zIndex: 2,
      }}>
        <span style={{
          width: 7, height: 7, background: C.green, borderRadius: '50%',
          animation: 'lp 2s ease infinite',
          boxShadow: `0 0 8px ${C.green}`,
        }} />
        LIVE · PRODUCTION READY · v1.0
      </div>

      {/* Title */}
      <h1 style={{
        fontFamily: "'Playfair Display', serif",
        fontSize: 'clamp(52px,9vw,108px)',
        fontWeight: 900, lineHeight: .95, letterSpacing: -3,
        position: 'relative', zIndex: 2,
      }}>
        <span style={{ display: 'block', color: C.ink }}>فكّر مرة واحدة.</span>
        <span style={{
          display: 'block', color: C.gold, position: 'relative',
        }}>
          نفّذ كل شيء.
          <span style={{
            content: '""', position: 'absolute', bottom: -6, right: 0, left: 0, height: 3,
            background: `linear-gradient(90deg,transparent,${C.gold},transparent)`,
          }} />
        </span>
      </h1>

      <p style={{
        marginTop: 28, fontSize: 'clamp(13px,1.8vw,17px)', color: C.muted,
        maxWidth: 500, lineHeight: 1.9, position: 'relative', zIndex: 2,
      }}>
        مساعد ذكاء اصطناعي يفهم هدفك، يبني خطة تنفيذ تلقائية،
        ويستخدم <strong style={{ color: C.txt, fontWeight: 600 }}>أنسب أداة</strong> لكل مهمة — بدون أي إعداد منك.
      </p>

      {/* Buttons */}
      <div style={{
        marginTop: 36, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap',
        position: 'relative', zIndex: 2,
      }}>
        <a href="/chat" style={{
          padding: '13px 30px', background: C.ink, color: C.paper,
          border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer',
          textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 9,
          transition: 'all .25s', fontFamily: "'Noto Kufi Arabic', sans-serif", letterSpacing: .3,
        }} onMouseEnter={e => { e.currentTarget.style.background = C.gold; e.currentTarget.style.color = C.ink; e.currentTarget.style.transform = 'translateY(-2px)' }}
           onMouseLeave={e => { e.currentTarget.style.background = C.ink; e.currentTarget.style.color = C.paper; e.currentTarget.style.transform = 'translateY(0)' }}>
          ابدأ مجاناً ←
        </a>
        <a href="#how" style={{
          padding: '13px 30px', background: 'transparent', color: C.muted,
          border: `1.5px solid ${C.line}`, borderRadius: 10, fontSize: 13, cursor: 'pointer',
          textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 9,
          transition: 'all .25s', fontFamily: "'Noto Kufi Arabic', sans-serif",
        }} onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.color = C.txt }}
           onMouseLeave={e => { e.currentTarget.style.borderColor = C.line; e.currentTarget.style.color = C.muted }}>
          كيف يعمل؟
        </a>
      </div>

      {/* Stats */}
      <div style={{
        display: 'flex', marginTop: 64, position: 'relative', zIndex: 2,
        background: C.ink, borderRadius: 16, overflow: 'hidden', maxWidth: 700, width: '100%',
        boxShadow: '0 24px 48px rgba(0,0,0,.15)',
      }}>
        {[
          { n: '24', s: '+', l: 'AI TOOLS' },
          { n: '62', s: '+', l: 'MODULES' },
          { n: '<3', s: 's', l: 'RESPONSE' },
          { n: '$0', s: '.01', l: 'AVG COST' },
        ].map((stat, i) => (
          <div key={i} style={{
            flex: 1, padding: '20px 18px', textAlign: 'center',
            borderLeft: i > 0 ? `1px solid ${C.line2}` : 'none',
          }}>
            <div style={{
              fontFamily: "'Playfair Display', serif", fontSize: 30, fontWeight: 900,
              color: C.paper, lineHeight: 1,
            }}>
              {stat.n}<span style={{ color: C.gold }}>{stat.s}</span>
            </div>
            <div style={{
              fontSize: 9, color: C.stone2, marginTop: 5,
              fontFamily: "'DM Mono', monospace", letterSpacing: .8,
            }}>
              {stat.l}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function HowItWorks() {
  const stepsRef = useRef<(HTMLDivElement | null)[]>([])

  useEffect(() => {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) e.target.classList.add('on')
      })
    }, { threshold: .1 })
    stepsRef.current.forEach(el => { if (el) obs.observe(el) })
    return () => obs.disconnect()
  }, [])

  const steps = [
    { n: '01', h: 'يفهم ما تريد', d: 'يحلل طلبك ويحدد نوعه تلقائياً — كود، بحث، تحليل، تخطيط — بدقة عالية.', tag: 'AI Understanding · Auto-detect' },
    { n: '02', h: 'يبني خطة التنفيذ', d: 'يقسّم هدفك لمهام متوازية ويوزعها على الأدوات المناسبة في نفس الوقت.', tag: 'Parallel Execution · Smart Planning' },
    { n: '03', h: 'يختار الأداة الأذكى', d: 'نموذج محلي مجاني للمهام البسيطة، نموذج متقدم للمعقدة — بتكلفة أقل من سنت.', tag: 'Smart Routing · Cost-aware' },
    { n: '04', h: 'يتذكر كل شيء', d: 'ذاكرة دائمة عبر كل المحادثات — يتذكر تفضيلاتك وقراراتك السابقة.', tag: 'Persistent Memory · Always learning' },
  ]

  return (
    <section id="how" style={{ padding: '96px 48px', maxWidth: 1160, margin: '0 auto' }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: C.gold, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 14 }}>
        HOW IT WORKS
      </div>
      <h2 style={{
        fontFamily: "'Playfair Display', serif", fontSize: 'clamp(28px,4vw,50px)',
        fontWeight: 900, letterSpacing: -1, lineHeight: 1.1, marginBottom: 14,
      }}>
        أربع خطوات.<br />نتيجة كاملة.
      </h2>
      <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.9, maxWidth: 460 }}>
        من أول كلمة تكتبها حتى النتيجة النهائية — النظام يدير كل شيء.
      </p>

      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 56, marginTop: 52, alignItems: 'start',
      }}>
        {/* Steps */}
        <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: 0 }}>
          <div style={{
            position: 'absolute', right: 20, top: 28, bottom: 28,
            width: 1, background: `linear-gradient(to bottom,${C.gold},${C.line},transparent)`,
          }} />
          {steps.map((s, i) => (
            <div key={i} ref={el => { stepsRef.current[i] = el }} className="step" style={{
              display: 'flex', gap: 20, alignItems: 'flex-start', padding: '20px 0',
              opacity: 0, transform: 'translateX(-14px)', transition: 'all .55s ease',
            }}>
              <div style={{
                width: 42, height: 42, borderRadius: '50%', background: C.ink,
                border: `2px solid ${C.gold}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: "'DM Mono', monospace", fontSize: 12, color: C.gold,
                flexShrink: 0, position: 'relative', zIndex: 1,
              }}>
                {s.n}
              </div>
              <div style={{ paddingTop: 9 }}>
                <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 17, fontWeight: 700, marginBottom: 5, color: C.ink }}>
                  {s.h}
                </div>
                <div style={{ fontSize: 12, color: C.muted, lineHeight: 1.8 }}>{s.d}</div>
                <div style={{
                  display: 'inline-block', marginTop: 7, padding: '2px 9px',
                  background: C.golddim, border: `1px solid ${C.gold}`, borderRadius: 5,
                  fontSize: 9, color: C.gold, fontFamily: "'DM Mono', monospace", letterSpacing: .5,
                }}>
                  {s.tag}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Terminal */}
        <div style={{
          background: C.ink, borderRadius: 14, overflow: 'hidden',
          boxShadow: '0 40px 80px rgba(0,0,0,.25)',
        }}>
          <div style={{
            padding: '11px 14px', background: '#111118', borderBottom: `1px solid ${C.line2}`,
            display: 'flex', alignItems: 'center', gap: 7,
          }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#FF5F57' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#FFBD2E' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#28C840' }} />
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 9, color: '#3A3828', marginRight: 'auto' }}>
              jnus · live session
            </span>
          </div>
          <div style={{ padding: '18px 20px', fontFamily: "'DM Mono', monospace", fontSize: 11, lineHeight: 2.1 }}>
            <div><span style={{ color: C.gold }}>أنت ← </span><span style={{ color: C.paper }}>ابني REST API بـ JWT authentication</span></div>
            <div style={{ height: 8 }} />
            <div><span style={{ color: C.stone2 }}>◐ تحليل الطلب... </span><span style={{ color: C.green }}>✓ كود — دقة 97%</span></div>
            <div><span style={{ color: C.stone2 }}>◐ الأداة المختارة: </span><span style={{ color: '#7DD3FC' }}>Code Agent + Review Agent</span></div>
            <div><span style={{ color: C.stone2 }}>◐ مهام متوازية: </span><span style={{ color: '#7DD3FC' }}>3</span></div>
            <div style={{ height: 8 }} />
            <div><span style={{ color: C.green }}>✓ </span><span style={{ color: C.stone2 }}>auth/models.py — User + JWT schema</span></div>
            <div><span style={{ color: C.green }}>✓ </span><span style={{ color: C.stone2 }}>auth/router.py — /login /register /refresh</span></div>
            <div><span style={{ color: C.green }}>✓ </span><span style={{ color: C.stone2 }}>auth/middleware.py — Token validation</span></div>
            <div><span style={{ color: C.green }}>✓ </span><span style={{ color: C.stone2 }}>tests/ — 12 unit tests</span></div>
            <div style={{ height: 8 }} />
            <div><span style={{ color: C.gold2 }}>التكلفة: $0.006 · الوقت: 3.8 ثانية</span></div>
            <div style={{ height: 8 }} />
            <div><span style={{ color: C.gold }}>أنت ← </span><span style={{
              display: 'inline-block', width: 7, height: 13, background: C.gold,
              animation: 'blink 1s step-end infinite', verticalAlign: 'middle',
            }} /></div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Capabilities() {
  const cardsRef = useRef<(HTMLDivElement | null)[]>([])

  useEffect(() => {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) e.target.classList.add('on')
      })
    }, { threshold: .1 })
    cardsRef.current.forEach(el => { if (el) obs.observe(el) })
    return () => obs.disconnect()
  }, [])

  return (
    <section id="capabilities" style={{ padding: '96px 48px', maxWidth: 1160, margin: '0 auto' }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: C.gold, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 14 }}>
        CAPABILITIES
      </div>
      <h2 style={{
        fontFamily: "'Playfair Display', serif", fontSize: 'clamp(28px,4vw,50px)',
        fontWeight: 900, letterSpacing: -1, lineHeight: 1.1, marginBottom: 14,
      }}>
        مبني للإنتاج<br />من اليوم الأول
      </h2>
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))',
        gap: 14, marginTop: 48,
      }}>
        {CAPS.map((c, i) => (
          <div key={i} ref={el => { cardsRef.current[i] = el }} className="cap-card" style={{
            padding: 24, background: '#fff', border: `1px solid ${C.line}`,
            borderRadius: 14, transition: 'all .25s',
            opacity: 0, transform: 'translateY(16px)',
            transitionDelay: `${i * 0.07}s`,
          }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.boxShadow = '0 8px 32px rgba(201,168,76,.12)'; e.currentTarget.style.transform = 'translateY(-3px)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = C.line; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translateY(0)' }}
          >
            <div style={{ fontSize: 26, marginBottom: 14 }}>{c.i}</div>
            <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 16, fontWeight: 700, marginBottom: 7, color: C.ink }}>
              {c.h}
            </div>
            <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.8 }}>{c.d}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

function CtaSection() {
  return (
    <div style={{
      textAlign: 'center', padding: '100px 40px', position: 'relative', overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse 60% 60% at 50% 50%,${C.golddim},transparent)`,
        pointerEvents: 'none',
      }} />
      <h2 style={{
        fontFamily: "'Playfair Display', serif", fontSize: 'clamp(32px,5vw,62px)',
        fontWeight: 900, letterSpacing: -1.5, lineHeight: 1.05, marginBottom: 18,
        position: 'relative', zIndex: 1,
      }}>
        جاهز تبدأ؟
      </h2>
      <p style={{
        fontSize: 13, color: C.muted, maxWidth: 380, margin: '0 auto 30px',
        lineHeight: 1.9, position: 'relative', zIndex: 1,
      }}>
        اكتب هدفك الأول وشاهد النظام يفكر وينفذ أمامك مباشرة.
      </p>
      <a href="/chat" style={{
        padding: '15px 38px', background: C.ink, color: C.paper,
        border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: 'pointer',
        textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 9,
        transition: 'all .25s', fontFamily: "'Noto Kufi Arabic', sans-serif",
      }} onMouseEnter={e => { e.currentTarget.style.background = C.gold; e.currentTarget.style.color = C.ink; e.currentTarget.style.transform = 'translateY(-2px)' }}
         onMouseLeave={e => { e.currentTarget.style.background = C.ink; e.currentTarget.style.color = C.paper; e.currentTarget.style.transform = 'translateY(0)' }}>
        ابدأ مجاناً ←
      </a>
    </div>
  )
}

function Footer() {
  return (
    <footer style={{
      borderTop: `1px solid ${C.line}`, padding: '24px 48px',
      display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10,
    }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: C.muted }}>
        Jnus v1.0.0 · Powered by AI · Built on Cloudflare
      </div>
      <ul style={{ display: 'flex', gap: 18, listStyle: 'none', margin: 0, padding: 0 }}>
        <li><a href="https://github.com/Bishoysamyaziz/Jnus.1" target="_blank" style={{
          fontSize: 10, color: C.dim, textDecoration: 'none',
          fontFamily: "'DM Mono', monospace", transition: 'color .2s',
        }} onMouseEnter={e => e.currentTarget.style.color = C.muted}
           onMouseLeave={e => e.currentTarget.style.color = C.dim}>GitHub</a></li>
        <li><a href="#how" style={{
          fontSize: 10, color: C.dim, textDecoration: 'none',
          fontFamily: "'DM Mono', monospace", transition: 'color .2s',
        }} onMouseEnter={e => e.currentTarget.style.color = C.muted}
           onMouseLeave={e => e.currentTarget.style.color = C.dim}>Docs</a></li>
        <li><a href="/chat" style={{
          fontSize: 10, color: C.dim, textDecoration: 'none',
          fontFamily: "'DM Mono', monospace", transition: 'color .2s',
        }} onMouseEnter={e => e.currentTarget.style.color = C.muted}
           onMouseLeave={e => e.currentTarget.style.color = C.dim}>Chat</a></li>
      </ul>
    </footer>
  )
}

// ── MAIN PAGE ──────────────────────────────────────────────────────

export default function Home() {
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Noto+Kufi+Arabic:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
        body {
          background: ${C.paper};
          color: ${C.txt};
          font-family: 'Noto Kufi Arabic', sans-serif;
          overflow-x: hidden;
        }

        /* Noise overlay */
        body::after {
          content: '';
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 1000;
          opacity: .025;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)'/%3E%3C/svg%3E");
        }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${C.line}; border-radius: 2px; }

        @keyframes riseUp {
          from { opacity: 0; transform: translateY(22px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes lp {
          0%, 100% { opacity: 1; box-shadow: 0 0 8px ${C.green}; }
          50%      { opacity: .4; box-shadow: none; }
        }
        @keyframes blink {
          50% { opacity: 0; }
        }

        .step.on { opacity: 1 !important; transform: none !important; }
        .cap-card.on { opacity: 1 !important; transform: none !important; }

        @media (max-width: 768px) {
          nav { padding: 13px 18px !important; }
          .sec { padding: 56px 18px; }
          .how-grid { grid-template-columns: 1fr !important; }
          .h-stats { flex-wrap: wrap; }
          .hstat { flex: 1 1 44%; }
          footer { padding: 18px; flex-direction: column; text-align: center; }
        }
      `}</style>

      <Navbar />
      <main>
        <Hero />
        <div style={{ height: 1, background: `linear-gradient(90deg,transparent,${C.line},transparent)`, margin: '0 48px' }} />
        <HowItWorks />
        <div style={{ height: 1, background: `linear-gradient(90deg,transparent,${C.line},transparent)`, margin: '0 48px' }} />
        <Capabilities />
        <div style={{ height: 1, background: `linear-gradient(90deg,transparent,${C.line},transparent)`, margin: '0 48px' }} />
        <CtaSection />
      </main>
      <Footer />
    </>
  )
}
