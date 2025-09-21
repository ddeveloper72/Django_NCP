/**
 * Search and Test Utilities JavaScript
 * Handles common functionality for search results and test pages
 */

// Auto-dismiss Bootstrap alerts after a delay
function initializeAlertAutoDismiss(delay = 5000) {
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
        alerts.forEach(function (alert) {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, delay);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function () {
    console.log('🔍 Initializing Search/Test utilities...');

    // Initialize auto-dismiss for alerts (exclude danger alerts)
    initializeAlertAutoDismiss();

    console.log('✅ Search/Test utilities initialized successfully');
});
