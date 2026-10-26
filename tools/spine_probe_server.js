const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const NM = path.join(ROOT, '.tooling', 'node_modules');
const OUT = path.join(ROOT, 'art', 'phase1', 'reference_character');
const REF = path.join(ROOT, 'reference', 'character_sources', 'ark_models', '291_aglina');
const PORT = Number(process.env.SPINE_PROBE_PORT || 8173);

const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.skel': 'application/octet-stream',
  '.atlas': 'text/plain; charset=utf-8'
};

function sendFile(res, file, status = 200) {
  fs.readFile(file, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('not found: ' + file);
      return;
    }
    res.writeHead(status, {
      'Content-Type': types[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': 'no-store'
    });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('ok');
    return;
  }
  if (url.pathname === '/viewer') {
    return sendFile(res, path.join(__dirname, 'spine_viewer.html'));
  }
  if (url.pathname === '/vendor/pixi.js') {
    return sendFile(res, path.join(NM, 'pixi.js', 'dist', 'browser', 'pixi.js'));
  }
  if (url.pathname === '/vendor/pixi-spine.js') {
    return sendFile(res, path.join(NM, 'pixi-spine', 'dist', 'pixi-spine.umd.js'));
  }
  if (url.pathname.startsWith('/ref/')) {
    const name = path.basename(url.pathname);
    return sendFile(res, path.join(REF, name));
  }
  if (url.pathname === '/result' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body);
        fs.mkdirSync(OUT, { recursive: true });
        if (payload.inventory) {
          fs.writeFileSync(path.join(OUT, 'runtime_probe_inventory.json'), JSON.stringify(payload.inventory, null, 2) + '\n');
        }
        if (payload.log) {
          fs.writeFileSync(path.join(OUT, 'runtime_probe_log.txt'), payload.log);
        }
        if (payload.image && payload.image.startsWith('data:image/png;base64,')) {
          const b64 = payload.image.slice('data:image/png;base64,'.length);
          const name = (payload.name || 'probe').replace(/[^a-z0-9_.-]+/gi, '_');
          fs.writeFileSync(path.join(OUT, 'probe_' + name + '.png'), Buffer.from(b64, 'base64'));
        }
        if (Array.isArray(payload.images)) {
          for (const item of payload.images) {
            if (!item || !item.data || !item.data.startsWith('data:image/png;base64,')) continue;
            const b64 = item.data.slice('data:image/png;base64,'.length);
            const name = String(item.name || 'frame').replace(/[^a-z0-9_.-]+/gi, '_');
            fs.writeFileSync(path.join(OUT, 'probe_' + name + '.png'), Buffer.from(b64, 'base64'));
          }
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: String(err && err.stack || err) }));
      }
    });
    return;
  }
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('not found');
});

server.listen(PORT, '127.0.0.1', () => {
  console.log('spine probe server on http://127.0.0.1:' + PORT + '/viewer');
});
