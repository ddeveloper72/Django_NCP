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

/**
 * Pregnancy History Tab Navigation
 * Handles mobile-first tab switching for pregnancy history section
 */
function initializePregnancyHistoryTabs() {
    const pregnancyTabBtns = document.querySelectorAll('.pregnancy-tab-btn');
    const pregnancyTabPanes = document.querySelectorAll('.pregnancy-tab-pane');

    if (pregnancyTabBtns.length === 0) return;

    pregnancyTabBtns.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const targetTab = this.getAttribute('data-tab');

            // Remove active class from all buttons and panes
            pregnancyTabBtns.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
            });
            pregnancyTabPanes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked button and corresponding pane
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');
            const targetPane = document.getElementById(targetTab);
            if (targetPane) {
                targetPane.classList.add('active');
            }

            // Announce change to screen readers
            const announcement = `Switched to ${this.textContent.trim()} tab`;
            announceToScreenReader(announcement);
        });

        // Handle keyboard navigation
        btn.addEventListener('keydown', function (e) {
            let nextBtn = null;

            switch (e.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                    e.preventDefault();
                    nextBtn = this.nextElementSibling || pregnancyTabBtns[0];
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    nextBtn = this.previousElementSibling || pregnancyTabBtns[pregnancyTabBtns.length - 1];
                    break;
                case 'Home':
                    e.preventDefault();
                    nextBtn = pregnancyTabBtns[0];
                    break;
                case 'End':
                    e.preventDefault();
                    nextBtn = pregnancyTabBtns[pregnancyTabBtns.length - 1];
                    break;
            }

            if (nextBtn) {
                nextBtn.focus();
                nextBtn.click();
            }
        });
    });
}

/**
 * Announce changes to screen readers
 */
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    // Remove after announcement
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

// Initialize pregnancy history tabs when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    initializePregnancyHistoryTabs();
});

// Re-initialize if content is dynamically loaded
const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
        if (mutation.type === 'childList') {
            const addedNodes = Array.from(mutation.addedNodes);
            const hasPregnancyTabs = addedNodes.some(node =>
                node.nodeType === 1 &&
                (node.classList?.contains('pregnancy-tabs-container') ||
                    node.querySelector?.('.pregnancy-tabs-container'))
            );

            if (hasPregnancyTabs) {
                setTimeout(initializePregnancyHistoryTabs, 100);
            }
        }
    });
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});
