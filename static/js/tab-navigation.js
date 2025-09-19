/**
 * Tab Navigation JavaScript
 * Handles Bootstrap-style tab switching functionality
 * for the enhanced CDA components
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeTabNavigation();
});

function initializeTabNavigation() {
    // Find all tab navigation containers
    const tabContainers = document.querySelectorAll('.nav-tabs');

    tabContainers.forEach(container => {
        const tabLinks = container.querySelectorAll('a[data-tab-target]');

        tabLinks.forEach(link => {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                switchTab(this);
            });
        });

        // Initialize first tab as active if none are active
        const activeTab = container.querySelector('a.active');
        if (!activeTab && tabLinks.length > 0) {
            switchTab(tabLinks[0]);
        }
    });
}

function switchTab(activeTabLink) {
    const targetId = activeTabLink.getAttribute('data-tab-target');
    const tabContainer = activeTabLink.closest('.nav-tabs');
    const contentContainer = document.querySelector('.tab-content') ||
        tabContainer.parentElement.querySelector('[class*="tab-content"]') ||
        tabContainer.parentElement;

    // Remove active class from all tabs in this container
    const allTabLinks = tabContainer.querySelectorAll('a');
    allTabLinks.forEach(link => {
        link.classList.remove('active');
    });

    // Add active class to clicked tab
    activeTabLink.classList.add('active');

    // Hide all tab panes
    const allTabPanes = contentContainer.querySelectorAll('.tab-pane, [id*="tab-"]');
    allTabPanes.forEach(pane => {
        pane.style.display = 'none';
        pane.classList.remove('active');
    });

    // Show target tab pane
    const targetPane = document.getElementById(targetId);
    if (targetPane) {
        targetPane.style.display = 'block';
        targetPane.classList.add('active');

        // Add fade-in animation
        targetPane.style.opacity = '0';
        targetPane.style.transform = 'translateY(20px)';

        setTimeout(() => {
            targetPane.style.transition = 'all 0.3s ease-out';
            targetPane.style.opacity = '1';
            targetPane.style.transform = 'translateY(0)';
        }, 10);
    }

    // Trigger custom event for other scripts to listen to
    const event = new CustomEvent('tabSwitched', {
        detail: {
            activeTab: activeTabLink,
            targetId: targetId,
            targetPane: targetPane
        }
    });
    document.dispatchEvent(event);
}

// Utility function to programmatically switch to a tab
window.switchToTab = function (tabId) {
    const tabLink = document.querySelector(`a[data-tab-target="${tabId}"]`);
    if (tabLink) {
        switchTab(tabLink);
    }
};

// Utility function to get active tab
window.getActiveTab = function () {
    const activeTabLink = document.querySelector('.nav-tabs a.active');
    return activeTabLink ? activeTabLink.getAttribute('data-tab-target') : null;
};

// Handle browser back/forward navigation
window.addEventListener('popstate', function (event) {
    if (event.state && event.state.activeTab) {
        switchToTab(event.state.activeTab);
    }
});

// Optional: Add URL hash support
function handleHashChange() {
    const hash = window.location.hash.substring(1);
    if (hash) {
        const tabLink = document.querySelector(`a[data-tab-target="${hash}"]`);
        if (tabLink) {
            switchTab(tabLink);
        }
    }
}

window.addEventListener('hashchange', handleHashChange);

// Initialize hash on page load
if (window.location.hash) {
    setTimeout(handleHashChange, 100);
}
