/**
 * OneAgent OS — Cloudflare Backup Worker
 * =========================================
 * دوبلي احتياطي لتكوينات OneAgent OS على Cloudflare
 * هذا الـ Worker يخزن التكوينات الحساسة بشكل آمن
 * 
 * النسخة الاحتياطية من:
 * - Cloudflare Tokens (API, Deploy, User)
 * - DeepSeek API Key
 * - Account ID
 * - Deploy URLs
 */

// التكوينات مشفرة ومخزنة في Worker Variables
// يتم تعيينها عبر `wrangler secret put`

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Handle OPTIONS (preflight)
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: corsHeaders,
      });
    }

    // ── Health Check ──────────────────────────────────────────
    if (path === '/health' || path === '/') {
      return new Response(JSON.stringify({
        status: 'ok',
        service: 'OneAgent OS Backup Worker',
        version: env.BACKUP_VERSION || '1.0.0',
        timestamp: new Date().toISOString(),
      }), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });
    }

    // ── Get Backup Info ───────────────────────────────────────
    if (path === '/backup/info') {
      return new Response(JSON.stringify({
        service: 'OneAgent OS — Secure Config Backup',
        version: env.BACKUP_VERSION || '1.0.0',
        created_at: env.CREATED_AT || '2026-05-12',
        description: 'النسخة الاحتياطية الآمنة لتكوينات OneAgent OS على Cloudflare',
        endpoints: {
          health: '/health',
          info: '/backup/info',
          verify: '/backup/verify',
          config_summary: '/backup/config',
        },
      }), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });
    }

    // ── Verify Backup Status ──────────────────────────────────
    if (path === '/backup/verify') {
      const hasTokens = {
        account_id: !!env.CLOUDFLARE_ACCOUNT_ID,
        api_token: !!env.CLOUDFLARE_API_TOKEN,
        deploy_token: !!env.CLOUDFLARE_API_TOKEN_DEPLOY,
        deploy_token2: !!env.CLOUDFLARE_API_TOKEN_DEPLOY2,
        user_token: !!env.CLOUDFLARE_USER_TOKEN,
        deepseek_key: !!env.DEEPSEEK_API_KEY,
      };

      const allPresent = Object.values(hasTokens).every(v => v === true);

      return new Response(JSON.stringify({
        status: allPresent ? '✅ COMPLETE' : '⚠️ PARTIAL',
        all_tokens_present: allPresent,
        tokens: hasTokens,
        timestamp: new Date().toISOString(),
      }), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });
    }

    // ── Config Summary (بدون عرض التوكنات نفسها) ──────────────
    if (path === '/backup/config') {
      return new Response(JSON.stringify({
        cloudflare: {
          account_id: env.CLOUDFLARE_ACCOUNT_ID ? '✅ محفوظ' : '❌ غير محفوظ',
          api_token: env.CLOUDFLARE_API_TOKEN ? '✅ محفوظ' : '❌ غير محفوظ',
          deploy_token_primary: env.CLOUDFLARE_API_TOKEN_DEPLOY ? '✅ محفوظ' : '❌ غير محفوظ',
          deploy_token_secondary: env.CLOUDFLARE_API_TOKEN_DEPLOY2 ? '✅ محفوظ' : '❌ غير محفوظ',
          user_token: env.CLOUDFLARE_USER_TOKEN ? '✅ محفوظ' : '❌ غير محفوظ',
        },
        deepseek: {
          api_key: env.DEEPSEEK_API_KEY ? '✅ محفوظ' : '❌ غير محفوظ',
        },
        deploy_urls: {
          api_worker: 'https://oneagent-os-api.bishoysamyaziz.workers.dev',
          frontend: 'https://oneagent-os.pages.dev',
          backup_worker: url.origin,
        },
        timestamp: new Date().toISOString(),
      }), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });
    }

    // ── 404 ───────────────────────────────────────────────────
    return new Response(JSON.stringify({
      error: 'Not Found',
      available_endpoints: ['/health', '/backup/info', '/backup/verify', '/backup/config'],
    }), {
      status: 404,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders,
      },
    });
  },
};
