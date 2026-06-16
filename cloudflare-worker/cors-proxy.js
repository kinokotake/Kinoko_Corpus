/**
 * 自建 CORS 代理（部署到 Cloudflare Workers 免费版，每天 100,000 次请求额度）
 *
 * 部署步骤（无需安装任何工具，纯网页操作，约 3 分钟）：
 *   1. 打开 https://dash.cloudflare.com/ 免费注册/登录（不需要绑卡）。
 *   2. 左侧菜单进入 Workers & Pages → Create → Create Worker。
 *   3. 随便起个名字（例如 kinoko-cors），点 Deploy 生成初始模板。
 *   4. 点 Edit code，把模板代码全部删掉，粘贴本文件的内容，点右上角 Deploy。
 *   5. 部署成功后会得到一个形如 https://kinoko-cors.你的用户名.workers.dev 的网址。
 *   6. 回到 KINOKO 网站的「🔗 粘贴网址自动抓取技能文本」面板，展开
 *      「⚙️ 自定义跨域代理」，填入：
 *          https://kinoko-cors.你的用户名.workers.dev/?url={url}
 *      点击保存即可。之后抓取会优先走这个代理，比公共代理稳定得多。
 *
 * 用法：GET <worker地址>/?url=<目标网址（需要 encodeURIComponent）>
 */

export default {
  async fetch(request) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': '*',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const requestUrl = new URL(request.url);
    const target = requestUrl.searchParams.get('url');
    if (!target) {
      return new Response('Missing "url" query param', { status: 400, headers: corsHeaders });
    }

    let targetUrl;
    try {
      targetUrl = new URL(target);
    } catch (e) {
      return new Response('Invalid target url', { status: 400, headers: corsHeaders });
    }
    if (targetUrl.protocol !== 'http:' && targetUrl.protocol !== 'https:') {
      return new Response('Only http/https targets are allowed', { status: 400, headers: corsHeaders });
    }

    let upstream;
    try {
      upstream = await fetch(targetUrl.toString(), {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Accept-Language': 'ja,zh-CN;q=0.8,en;q=0.6',
        },
      });
    } catch (e) {
      return new Response('Upstream fetch failed: ' + e.message, { status: 502, headers: corsHeaders });
    }

    const body = await upstream.arrayBuffer();
    const headers = new Headers(corsHeaders);
    headers.set('Content-Type', upstream.headers.get('Content-Type') || 'text/html; charset=utf-8');
    return new Response(body, { status: upstream.status, headers });
  },
};
