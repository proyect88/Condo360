// ============================================
// Service Worker - Condo Services 360
// ============================================

const CACHE_NAME = 'condo-services-v32';
const STATIC_CACHE = 'static-v29';
const DYNAMIC_CACHE = 'dynamic-v29';

// Assets a cachear en instalación
const STATIC_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/css/responsive.css',
    '/static/css/admin.css',
    '/static/js/main.js',
    '/static/js/pwa.js',
    '/static/js/admin.js',
    '/static/js/testimonials-carousel.js',
    '/static/js/diagnostico-wizard.js',
    '/static/js/servicio-carrusel.js',
    '/static/js/home-diagnostico.js',
    '/manifest.json',
    '/offline.html',
    // Iconos
    '/static/images/icons/icon-72x72.png',
    '/static/images/icons/icon-96x96.png',
    '/static/images/icons/icon-128x128.png',
    '/static/images/icons/icon-144x144.png',
    '/static/images/icons/icon-152x152.png',
    '/static/images/icons/icon-192x192.png',
    '/static/images/icons/icon-384x384.png',
    '/static/images/icons/icon-512x512.png'
];

// Instalación - Cachear assets estáticos
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Cacheando assets estáticos');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activación - Limpiar caches viejos
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => {
                return Promise.all(
                    keys
                        .filter(key => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
                        .map(key => {
                            console.log('Eliminando cache:', key);
                            return caches.delete(key);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Estrategia de Cache: Stale-While-Revalidate
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);

    // Ignorar peticiones a APIs y terceros
    if (url.pathname.startsWith('/api/') ||
        url.hostname.includes('google-analytics') ||
        url.hostname.includes('facebook.com') ||
        url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('cdnjs.cloudflare.com')) {
        return event.respondWith(fetch(request));
    }

    // Estrategia para navegación (páginas)
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Cachear la página para uso offline
                    const clone = response.clone();
                    caches.open(DYNAMIC_CACHE).then(cache => {
                        cache.put(request, clone);
                    });
                    return response;
                })
                .catch(() => {
                    // Si falla, buscar en cache
                    return caches.match(request)
                        .then(cachedResponse => {
                            if (cachedResponse) return cachedResponse;
                            // Si no hay cache, mostrar página offline
                            return caches.match('/offline.html');
                        });
                })
        );
        return;
    }

    // Estrategia para assets estáticos: Network-First.
    // Asi los cambios de estilo se ven en el primer refresco; el cache
    // solo se usa cuando no hay conexion.
    event.respondWith(
        fetch(request)
            .then(networkResponse => {
                const clone = networkResponse.clone();
                caches.open(DYNAMIC_CACHE).then(cache => {
                    cache.put(request, clone);
                });
                return networkResponse;
            })
            .catch(() =>
                caches.match(request).then(cachedResponse => {
                    if (cachedResponse) return cachedResponse;
                    // Sin red y sin cache: fallback para imagenes
                    if (request.url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/)) {
                        return caches.match('/static/images/placeholder.jpg');
                    }
                    return new Response('No hay conexión a internet', {
                        status: 503,
                        statusText: 'Service Unavailable'
                    });
                })
            )
    );
});

// ============================================
// Push Notifications
// ============================================

self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    
    const options = {
        body: data.body || 'Nuevo mensaje de Condo Services 360',
        icon: '/static/images/icons/icon-192x192.png',
        badge: '/static/images/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        sound: '/static/sounds/notification.mp3',
        data: {
            url: data.url || '/',
            ticketId: data.ticketId,
            type: data.type || 'general'
        },
        actions: [
            {
                action: 'open',
                title: 'Ver detalles'
            },
            {
                action: 'close',
                title: 'Cerrar'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'Condo Services 360', options)
    );
});

// Manejo de click en notificaciones
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'close') {
        return;
    }

    const url = event.notification.data?.url || '/';
    const ticketId = event.notification.data?.ticketId;

    let targetUrl = url;
    if (ticketId) {
        targetUrl = `/admin/tickets/${ticketId}`;
    }

    event.waitUntil(
        self.clients.matchAll({ type: 'window' })
            .then(windowClients => {
                // Si hay una ventana abierta, enfocarla
                for (let client of windowClients) {
                    if (client.url === targetUrl && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Si no, abrir nueva
                if (self.clients.openWindow) {
                    return self.clients.openWindow(targetUrl);
                }
            })
    );
});

// ============================================
// Background Sync
// ============================================

self.addEventListener('sync', event => {
    if (event.tag === 'sync-tickets') {
        event.waitUntil(syncTickets());
    }
});

async function syncTickets() {
    try {
        const cache = await caches.open('offline-tickets');
        const requests = await cache.keys();
        
        for (const request of requests) {
            const response = await cache.match(request);
            if (response) {
                const data = await response.json();
                // Reenviar al servidor
                await fetch('/api/tickets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                await cache.delete(request);
            }
        }
    } catch (error) {
        console.error('Error en sync:', error);
    }
}

// ============================================
// Version Updates
// ============================================

self.addEventListener('message', event => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
});

console.log('Service Worker - Condo Services 360');
