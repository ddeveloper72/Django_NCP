/**
 * Service Worker for EU NCP Portal
 * Provides offline functionality and asset caching
 */

const CACHE_NAME = 'eu-ncp-portal-v1.0.0';
const OFFLINE_URL = '/offline/';

// Assets to cache immediately
const CORE_ASSETS = [
    '/',
    '/dashboard/',
    '/static/vendor/bootstrap/bootstrap.min.css',
    '/static/vendor/bootstrap/bootstrap.bundle.min.js',
    '/static/vendor/fontawesome/fontawesome.min.css',
    '/static/css/irish-healthcare-theme.css',
    '/static/css/bootstrap-components.css',
    '/static/css/main.css',
    '/static/js/base.js',
    '/static/js/navigation.js',
    '/static/manifest.json',
    OFFLINE_URL
];

// Install event - cache core assets
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching core assets');
                return cache.addAll(CORE_ASSETS);
            })
            .then(() => {
                console.log('Service Worker: Core assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Service Worker: Failed to cache core assets', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');

    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activated successfully');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip Chrome extensions and other non-http(s) requests
    if (!event.request.url.startsWith('http')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                // Return cached version if available
                if (cachedResponse) {
                    console.log('Service Worker: Serving from cache', event.request.url);
                    return cachedResponse;
                }

                // Try network request
                return fetch(event.request)
                    .then(response => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone response for caching
                        const responseToCache = response.clone();

                        // Cache the response for future use
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                // Only cache certain types of requests
                                if (shouldCache(event.request)) {
                                    console.log('Service Worker: Caching new resource', event.request.url);
                                    cache.put(event.request, responseToCache);
                                }
                            });

                        return response;
                    })
                    .catch(() => {
                        // Network failed, serve offline page for navigate requests
                        if (event.request.mode === 'navigate') {
                            console.log('Service Worker: Serving offline page');
                            return caches.match(OFFLINE_URL);
                        }

                        // For other requests, try to serve a cached version
                        return caches.match('/static/images/offline-icon.png');
                    });
            })
    );
});

// Determine if a request should be cached
function shouldCache(request) {
    const url = new URL(request.url);

    // Cache static assets
    if (url.pathname.startsWith('/static/')) {
        return true;
    }

    // Cache main pages
    const cachedPaths = ['/', '/dashboard/', '/patient/', '/about/'];
    if (cachedPaths.includes(url.pathname)) {
        return true;
    }

    // Don't cache API calls or dynamic content
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin/')) {
        return false;
    }

    return false;
}

// Handle background sync for form submissions
self.addEventListener('sync', event => {
    if (event.tag === 'patient-form-sync') {
        console.log('Service Worker: Background sync for patient forms');
        event.waitUntil(syncPatientForms());
    }
});

// Sync patient forms when connection is restored
async function syncPatientForms() {
    try {
        // Get pending forms from IndexedDB
        const pendingForms = await getPendingForms();

        for (const form of pendingForms) {
            try {
                const response = await fetch('/api/patient/submit/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': form.csrfToken
                    },
                    body: JSON.stringify(form.data)
                });

                if (response.ok) {
                    console.log('Service Worker: Form synced successfully', form.id);
                    await removePendingForm(form.id);
                }
            } catch (error) {
                console.error('Service Worker: Failed to sync form', form.id, error);
            }
        }
    } catch (error) {
        console.error('Service Worker: Sync operation failed', error);
    }
}

// Push notification handling
self.addEventListener('push', event => {
    console.log('Service Worker: Push notification received');

    const options = {
        body: event.data ? event.data.text() : 'New healthcare notification',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        tag: 'eu-ncp-notification',
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/icons/view-action.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/icons/dismiss-action.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('EU NCP Portal', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Notification clicked', event.action);

    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/dashboard/')
        );
    }
});

// Utility functions for IndexedDB operations
async function getPendingForms() {
    // Implementation would depend on IndexedDB setup
    return [];
}

async function removePendingForm(formId) {
    // Implementation would depend on IndexedDB setup
    console.log('Removing pending form:', formId);
}
