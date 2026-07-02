/**
 * Service Worker for Beyond Career Dashboard
 * Handles caching and offline functionality
 * Production-ready: Logs only in development mode
 */

const CACHE_NAME = 'beyond-career-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/dashboard/css/style.css',
  '/dashboard/css/footer-pagination.css',
  '/dashboard/js/main.js',
  '/dashboard/js/utils.js',
  '/dashboard/js/sparkles.js',
  '/dashboard/js/api.js',
  '/dashboard/js/combo-box.js',
  '/dashboard/js/animated-loading-skeleton.js',
  '/dashboard/js/dot-pattern.js',
  '/dashboard/js/footer-dot-pattern.js'
];

// Only log in development mode
const isDev = false; // Set to true for development
const log = (message) => {
  if (isDev) {
    console.log(`[SW] ${message}`);
  }
};

// Install event - cache assets
self.addEventListener('install', (event) => {
  log('Service worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      log('Caching assets...');
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        log(`Cache error: ${err}`);
        // Don't fail installation if some assets can't be cached
        return Promise.resolve();
      });
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  log('Service worker activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            log(`Deleting old cache: ${cacheName}`);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip API calls - always fetch from network
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Don't cache API responses
          return response;
        })
        .catch(() => {
          // Return offline response for API calls
          return new Response(
            JSON.stringify({ error: 'Offline' }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
          );
        })
    );
    return;
  }

  // For static assets, use cache-first strategy
  event.respondWith(
    caches.match(request).then((response) => {
      if (response) {
        log(`Serving from cache: ${url.pathname}`);
        return response;
      }

      return fetch(request)
        .then((response) => {
          // Cache successful responses
          if (response && response.status === 200) {
            const responseToCache = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          // Return offline page or cached fallback
          log(`Failed to fetch: ${url.pathname}`);
          return caches.match('/index.html');
        });
    })
  );
});
