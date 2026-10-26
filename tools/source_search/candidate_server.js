// Static server for runtime-parsing downloaded Ark-Models candidates.
// Serves only tools/source_search/work/<id>/ plus the pinned pixi/pixi-spine builds.
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const NM = path.join(ROOT, '.tooling', 'node_modules');
const WORK = path.join(__dirname, 'work');
const PORT = Number(process.env.CANDIDATE_PORT || 8174);

const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.skel': 'application/octet-stream',
  '.atlas': 'text/plain; charset=utf-8'
};

function sendFile(res, file) {
  fs.readFile(file, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('not found: ' + path.relative(ROOT, file));
      return;
    }
    res.writeHead(200, {
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
    return sendFile(res, path.join(__dirname, 'candidate_viewer.html'));
  }
  if (url.pathname === '/vendor/pixi.js') {
    return sendFile(res, path.join(NM, 'pixi.js', 'dist', 'browser', 'pixi.js'));
  }
  if (url.pathname === '/vendor/pixi-spine.js') {
    return sendFile(res, path.join(NM, 'pixi-spine', 'dist', 'pixi-spine.umd.js'));
  }
  if (url.pathname.startsWith('/model/')) {
    const parts = url.pathname.split('/').filter(Boolean);
    if (parts.length !== 3) {
      res.writeHead(400).end('bad model path');
      return;
    }
    const id = path.basename(parts[1]);
    const name = path.basename(parts[2]);
    return sendFile(res, path.join(WORK, id, name));
  }
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('not found');
});

server.listen(PORT, '127.0.0.1', () => {
  console.log('candidate runtime server on http://127.0.0.1:' + PORT + '/viewer?id=<candidate>');
});
