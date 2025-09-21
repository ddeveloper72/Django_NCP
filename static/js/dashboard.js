/**
 * Dashboard JavaScript
 * Handles SMP dashboard functionality and European SMP synchronization
 */

// Get CSRF token from cookie utility
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// European SMP Synchronization
async function syncWithEuropeanSMP() {
    const resultDiv = document.getElementById('sync-result');
    const button = event.target;

    button.textContent = '🔄 Syncing...';
    button.disabled = true;

    try {
        // Get sync URL and CSRF token from global config or use defaults
        const config = window.dashboardConfig || {};
        const syncUrl = config.europeanSmpSyncUrl || window.europeanSMPSyncURL || '/smp_client/european_smp_sync/';
        const csrfToken = config.csrfToken || getCookie('csrftoken');

        const response = await fetch(syncUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    ✅ Sync completed! Synced ${data.synced_participants} participants.
                </div>
            `;
            setTimeout(() => location.reload(), 2000);
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    ❌ Sync failed: ${data.error}
                </div>
            `;
        }
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                ❌ Network error: ${error.message}
            </div>
        `;
    }

    button.textContent = '🔄 Sync with European SMP';
    button.disabled = false;
}

// Dashboard Statistics Animation (for standalone dashboard)
function animateStatNumbers() {
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(stat => {
        const target = parseInt(stat.textContent) || 0;
        let current = 0;
        const increment = target / 20;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                stat.textContent = target;
                clearInterval(timer);
            } else {
                stat.textContent = Math.floor(current);
            }
        }, 50);
    });
}

// Initialize dashboard functionality
document.addEventListener('DOMContentLoaded', function () {
    console.log('📊 Initializing Dashboard functionality...');

    // Initialize stat animations if elements exist
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues.length > 0) {
        animateStatNumbers();
    }

    console.log('✅ Dashboard initialized successfully');
});

// Make sync function globally available for template usage
window.syncWithEuropeanSMP = syncWithEuropeanSMP;
