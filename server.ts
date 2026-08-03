import http from "http";
import { spawn } from "child_process";

const PORT = 3000;
const TARGET_PORT = 8000;

console.log("Spawning Django backend server...");
const django = spawn("python3", ["manage.py", "runserver", `127.0.0.1:${TARGET_PORT}`], {
  stdio: "inherit"
});

django.on("error", (err) => {
  console.error("❌ Failed to start Django process:", err);
});

process.on("exit", () => {
  django.kill();
});

// Create a transparent reverse proxy
const server = http.createServer((req, res) => {
  const options = {
    hostname: "127.0.0.1",
    port: TARGET_PORT,
    path: req.url,
    method: req.method,
    headers: req.headers,
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 500, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  req.pipe(proxyReq, { end: true });

  proxyReq.on("error", (err) => {
    console.error("Proxy error:", err.message);
    res.writeHead(502, { "Content-Type": "text/plain" });
    res.end("Bad Gateway: Django server is starting up or unreachable.");
  });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`🚀 Node.js transparent proxy running on http://0.0.0.0:${PORT} -> Django on port ${TARGET_PORT}`);
});
