// Serves the game under /games/grainy/ by stripping that prefix and handing the
// request to the static-asset binding (worker/public: index.html, ref.webp).
const PREFIX = '/games/grainy';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === PREFIX) {                       // /games/grainy → /games/grainy/
      return Response.redirect(`${url.origin}${PREFIX}/${url.search}`, 301);
    }
    if (!url.pathname.startsWith(PREFIX + '/')) return new Response('Not found', { status: 404 });

    const assetUrl = new URL(request.url);
    assetUrl.pathname = url.pathname.slice(PREFIX.length) || '/';
    if (assetUrl.pathname === '/index.html') assetUrl.pathname = '/';   // the assets binding serves index.html at /

    const res = await env.ASSETS.fetch(new Request(assetUrl, request));
    const out = new Response(res.body, res);
    out.headers.set('Cache-Control', 'public, max-age=300');
    out.headers.set('X-Content-Type-Options', 'nosniff');
    return out;
  },
};
