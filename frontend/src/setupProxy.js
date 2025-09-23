const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Get the backend URL from environment variable
  // For local development, use localhost:8000
  // For production on Hostinger, backend runs on internal network
  const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  app.use(
    '/health',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/debug',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/debug/tasks',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/logs',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/upload',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/task',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/output',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/result',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/cleanup',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/start-processing',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
  
  app.use(
    '/api',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
    })
  );
};
