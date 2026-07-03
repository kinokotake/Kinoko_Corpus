/**
 * Kinoko Auth + CORS Worker
 *
 * ── 升级步骤（原有代理不受影响）──────────────────────────────
 * 1. 在 Cloudflare 控制台 Workers & Pages → KV → Create namespace
 *    命名为 KINOKO（随意，只要记住）
 * 2. 进入 Worker → Settings → Variables → KV Namespace Bindings
 *    Name 填 KINOKO_KV，选刚才创建的命名空间 → Save
 * 3. 同页面 → Variables → Add variable（类型选 Secret）
 *    Name 填 ADMIN_KEY，Value 填你设置的管理员密码 → Save
 * 4. 把本文件粘贴到 Worker 编辑器 → Deploy
 *
 * ── API 端点 ─────────────────────────────────────────────────
 *   GET  /?url=...              原有 CORS 代理（不变）
 *   POST /auth/login            用户登录，返回 {ok, name}
 *   POST /auth/ping             活动记录（搜索行为）
 *   GET  /admin/stats?ak=...    查看所有用户及使用统计
 *   POST /admin/add-user?ak=... 添加用户，返回生成的访问码
 *   POST /admin/del-user?ak=... 启用/停用用户（toggle）
 */

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function jsonResp(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS, 'Content-Type': 'application/json' },
  });
}

function genKey() {
  const chars = 'abcdefghjkmnpqrstuvwxyz23456789';
  let k = 'ki-';
  for (let i = 0; i < 10; i++) k += chars[Math.floor(Math.random() * chars.length)];
  return k;
}

function isAdmin(url, env) {
  const ak = url.searchParams.get('ak');
  return ak && env.ADMIN_KEY && ak === env.ADMIN_KEY;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS });
    }

    // ── POST /auth/login ────────────────────────────────────────
    if (url.pathname === '/auth/login' && request.method === 'POST') {
      if (!env.KINOKO_KV)
        return jsonResp({ ok: false, error: 'KV not bound (see setup instructions)' }, 500);

      const body = await request.json().catch(() => ({}));
      const key = (body.key || '').trim();
      if (!key) return jsonResp({ ok: false, error: 'missing key' }, 400);

      const user = await env.KINOKO_KV.get('user:' + key, { type: 'json' });
      if (!user || !user.active) return jsonResp({ ok: false, error: 'invalid key' }, 401);

      const now = new Date().toISOString();
      const usage = (await env.KINOKO_KV.get('usage:' + key, { type: 'json' })) || {};
      usage.name          = user.name;
      usage.last_seen     = now;
      usage.total_logins  = (usage.total_logins || 0) + 1;
      await env.KINOKO_KV.put('usage:' + key, JSON.stringify(usage));

      return jsonResp({ ok: true, name: user.name });
    }

    // ── POST /auth/ping ─────────────────────────────────────────
    if (url.pathname === '/auth/ping' && request.method === 'POST') {
      if (!env.KINOKO_KV) return jsonResp({ ok: false }, 200);

      const body = await request.json().catch(() => ({}));
      const key = (body.key || '').trim();
      if (!key) return jsonResp({ ok: false }, 200);

      const user = await env.KINOKO_KV.get('user:' + key, { type: 'json' });
      if (!user || !user.active) return jsonResp({ ok: false }, 200);

      const now = new Date().toISOString();
      const usage = (await env.KINOKO_KV.get('usage:' + key, { type: 'json' })) || {};
      usage.name      = user.name;
      usage.last_seen = now;
      if (body.action === 'search') {
        usage.total_searches = (usage.total_searches || 0) + 1;
        if (body.q) usage.last_query = String(body.q).slice(0, 200);
      }
      await env.KINOKO_KV.put('usage:' + key, JSON.stringify(usage));

      return jsonResp({ ok: true });
    }

    // ── GET /admin/stats ────────────────────────────────────────
    if (url.pathname === '/admin/stats') {
      if (!isAdmin(url, env)) return jsonResp({ error: 'unauthorized' }, 403);
      if (!env.KINOKO_KV) return jsonResp({ error: 'KV not bound' }, 500);

      const listed = await env.KINOKO_KV.list({ prefix: 'user:' });
      const users = [];
      for (const k of listed.keys) {
        const user = await env.KINOKO_KV.get(k.name, { type: 'json' });
        if (!user) continue;
        const usage = (await env.KINOKO_KV.get('usage:' + user.key, { type: 'json' })) || {};
        users.push({
          key:            user.key,
          name:           user.name,
          note:           user.note || '',
          created:        user.created,
          active:         user.active,
          last_seen:      usage.last_seen    || null,
          total_logins:   usage.total_logins  || 0,
          total_searches: usage.total_searches || 0,
          last_query:     usage.last_query    || '',
        });
      }
      users.sort((a, b) => (b.last_seen || '').localeCompare(a.last_seen || ''));
      return jsonResp({ users });
    }

    // ── POST /admin/add-user ────────────────────────────────────
    if (url.pathname === '/admin/add-user' && request.method === 'POST') {
      if (!isAdmin(url, env)) return jsonResp({ error: 'unauthorized' }, 403);
      if (!env.KINOKO_KV) return jsonResp({ error: 'KV not bound' }, 500);

      const body = await request.json().catch(() => ({}));
      const name = (body.name || '').trim();
      if (!name) return jsonResp({ error: 'name required' }, 400);

      const key = genKey();
      const user = {
        key,
        name,
        note:    (body.note || '').trim(),
        created: new Date().toISOString(),
        active:  true,
      };
      await env.KINOKO_KV.put('user:' + key, JSON.stringify(user));
      return jsonResp({ ok: true, key, user });
    }

    // ── POST /admin/del-user ────────────────────────────────────
    if (url.pathname === '/admin/del-user' && request.method === 'POST') {
      if (!isAdmin(url, env)) return jsonResp({ error: 'unauthorized' }, 403);
      if (!env.KINOKO_KV) return jsonResp({ error: 'KV not bound' }, 500);

      const body = await request.json().catch(() => ({}));
      const key = (body.key || '').trim();
      const user = await env.KINOKO_KV.get('user:' + key, { type: 'json' });
      if (!user) return jsonResp({ error: 'not found' }, 404);

      user.active = !user.active;
      await env.KINOKO_KV.put('user:' + key, JSON.stringify(user));
      return jsonResp({ ok: true, active: user.active });
    }

    // ── 原有 CORS 代理 ──────────────────────────────────────────
    const target = url.searchParams.get('url');
    if (!target) {
      return new Response('kinoko-worker: missing ?url= param', { status: 400, headers: CORS });
    }

    let targetUrl;
    try { targetUrl = new URL(target); }
    catch { return new Response('Invalid target url', { status: 400, headers: CORS }); }

    if (targetUrl.protocol !== 'http:' && targetUrl.protocol !== 'https:') {
      return new Response('Only http/https targets allowed', { status: 400, headers: CORS });
    }

    let upstream;
    try {
      upstream = await fetch(targetUrl.toString(), {
        headers: {
          'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Accept-Language': 'ja,zh-CN;q=0.8,en;q=0.6',
        },
      });
    } catch (e) {
      return new Response('Upstream fetch failed: ' + e.message, { status: 502, headers: CORS });
    }

    const respBody = await upstream.arrayBuffer();
    const headers  = new Headers(CORS);
    headers.set('Content-Type', upstream.headers.get('Content-Type') || 'text/html; charset=utf-8');
    return new Response(respBody, { status: upstream.status, headers });
  },
};
