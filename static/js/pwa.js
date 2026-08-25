// ============================================
// PWA - Progressive Web App Configuration
// ============================================

// ============================================
// Service Worker Registration
// ============================================
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('Service Worker registrado:', registration);
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            console.log('Nueva versión disponible');
                            window.showNotification('Nueva versión disponible. Actualiza la app.', 'info');
                        }
                    });
                });
            })
            .catch(error => {
                console.error('Error al registrar Service Worker:', error);
            });
    });
}

// ============================================
// Install Prompt
// ============================================
// ============================================
// Instalacion PWA deshabilitada: no se muestra
// boton ni banner de instalacion
// ============================================
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
});

window.addEventListener('appinstalled', () => {
    console.log('App instalada exitosamente');
});

// ============================================
// Online/Offline Status
// ============================================
window.addEventListener('online', () => {
    document.body.classList.remove('offline');
    window.showNotification(' Conexión restablecida', 'success');
    // Recargar datos si es necesario
});

window.addEventListener('offline', () => {
    document.body.classList.add('offline');
    window.showNotification(' Sin conexión. Algunas funciones no están disponibles.', 'warning');
});

// ============================================
// Notifications Permission
// ============================================
if ('Notification' in window && navigator.serviceWorker) {
    // Verificar si ya tiene permisos
    if (Notification.permission === 'granted') {
        subscribeToPush();
    }
    
    // Botón para habilitar notificaciones
    document.getElementById('enableNotifications')?.addEventListener('click', async () => {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            subscribeToPush();
            window.showNotification(' Notificaciones activadas', 'success');
        } else {
            window.showNotification(' Notificaciones denegadas', 'warning');
        }
    });
}

async function subscribeToPush() {
    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array('TU_PUBLIC_VAPID_KEY_AQUI')
        });
        
        // Enviar suscripción al servidor
        const response = await fetch('/api/push/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(subscription)
        });
        
        if (response.ok) {
            console.log('Suscripción a push registrada');
        }
    } catch (error) {
        console.error('Error al suscribir a push:', error);
    }
}

// Helper: Convertir VAPID key
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// ============================================
// Manifest Check
// ============================================
fetch('/manifest.json')
    .then(response => {
        if (response.ok) {
            console.log('Manifest.json cargado correctamente');
        }
    })
    .catch(error => {
        console.error('Error al cargar manifest.json:', error);
    });

// ============================================
// Cache Management
// ============================================
// Función para limpiar caché manualmente
window.clearAppCache = async function() {
    if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
        console.log('Caché limpiado');
        window.showNotification('Caché limpiado correctamente', 'success');
    }
};

// ============================================
// Update Check
// ============================================
// Verificar actualizaciones cada hora
setInterval(() => {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(registration => {
            registration.update();
        });
    }
}, 3600000); // 1 hora

console.log('PWA - Condo Services 360 Inicializado');
