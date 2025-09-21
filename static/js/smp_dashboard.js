/**
 * SMP Dashboard JavaScript Module
 * Handles dashboard functionality and European SMP synchronization
 */

class SMPDashboard {
    constructor() {
        this.config = window.dashboardConfig || {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeAccessibility();
        console.log('SMP Dashboard initialized');
    }

    setupEventListeners() {
        // European SMP sync functionality
        const syncButton = document.querySelector('.sync-btn');
        if (syncButton) {
            syncButton.addEventListener('click', (e) => this.handleEuropeanSMPSync(e));
        }

        // Action card keyboard navigation
        const actionCards = document.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            const link = card.querySelector('.action-btn');
            if (link) {
                card.setAttribute('tabindex', '0');
                card.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        link.click();
                    }
                });
            }
        });
    }

    initializeAccessibility() {
        // Add ARIA labels to stat cards
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach((card, index) => {
            const number = card.querySelector('.stat-number');
            const label = card.querySelector('.stat-label');
            if (number && label) {
                card.setAttribute('aria-label', `${label.textContent}: ${number.textContent}`);
                card.setAttribute('role', 'status');
            }
        });

        // Enhance action cards accessibility
        const actionCards = document.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            const title = card.querySelector('h3');
            const description = card.querySelector('p');
            if (title) {
                const titleId = `action-title-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                title.id = titleId;
                card.setAttribute('aria-labelledby', titleId);

                if (description) {
                    const descId = `action-desc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                    description.id = descId;
                    card.setAttribute('aria-describedby', descId);
                }
            }
        });

        // Add semantic roles to sections
        const contentSections = document.querySelectorAll('.smp-content-section');
        contentSections.forEach(section => {
            section.setAttribute('role', 'region');
            const title = section.querySelector('.smp-section-title');
            if (title) {
                const titleId = `section-title-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                title.id = titleId;
                section.setAttribute('aria-labelledby', titleId);
            }
        });
    }

    async handleEuropeanSMPSync(event) {
        event.preventDefault();

        const button = event.target.closest('.sync-btn');
        const resultContainer = document.getElementById('sync-result');

        if (!button || !this.config.europeanSmpSyncUrl) {
            this.showSyncResult('Error: Sync configuration not found', 'error');
            return;
        }

        // Update button state
        const originalText = button.textContent;
        button.textContent = '🔄 Syncing...';
        button.disabled = true;
        button.setAttribute('aria-busy', 'true');

        try {
            const response = await fetch(this.config.europeanSmpSyncUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken || this.getCSRFToken(),
                },
                body: JSON.stringify({
                    source: 'european_smp'
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSyncResult(
                    `✅ Successfully synced ${data.participants_synced || 0} participants and ${data.services_synced || 0} services`,
                    'success'
                );

                // Update stats if available
                this.updateStats(data);
            } else {
                this.showSyncResult(`❌ Sync failed: ${data.error || 'Unknown error'}`, 'error');
            }

        } catch (error) {
            console.error('Sync error:', error);
            this.showSyncResult(`❌ Network error: ${error.message}`, 'error');
        } finally {
            // Restore button state
            button.textContent = originalText;
            button.disabled = false;
            button.removeAttribute('aria-busy');
        }
    }

    showSyncResult(message, type) {
        const resultContainer = document.getElementById('sync-result');
        if (!resultContainer) return;

        resultContainer.innerHTML = `
            <div class="sync-result ${type}" role="alert" aria-live="polite">
                ${message}
            </div>
        `;

        // Auto-hide after 10 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                if (resultContainer.querySelector('.sync-result.success')) {
                    resultContainer.innerHTML = '';
                }
            }, 10000);
        }
    }

    updateStats(data) {
        // Update participant count
        if (data.participant_count !== undefined) {
            const participantStat = document.querySelector('.stat-card:first-child .stat-number');
            if (participantStat) {
                this.animateNumberUpdate(participantStat, data.participant_count);
            }
        }

        // Update service count
        if (data.service_count !== undefined) {
            const serviceStat = document.querySelector('.stat-card:nth-child(2) .stat-number');
            if (serviceStat) {
                this.animateNumberUpdate(serviceStat, data.service_count);
            }
        }

        // Update endpoint count
        if (data.endpoint_count !== undefined) {
            const endpointStat = document.querySelector('.stat-card:nth-child(3) .stat-number');
            if (endpointStat) {
                this.animateNumberUpdate(endpointStat, data.endpoint_count);
            }
        }
    }

    animateNumberUpdate(element, newValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const increment = newValue > currentValue ? 1 : -1;
        const duration = 1000; // 1 second
        const steps = Math.abs(newValue - currentValue);
        const stepDuration = duration / Math.max(steps, 1);

        let current = currentValue;
        const timer = setInterval(() => {
            current += increment;
            element.textContent = current;

            if (current === newValue) {
                clearInterval(timer);
                // Flash effect to highlight change
                element.style.color = '#28a745';
                setTimeout(() => {
                    element.style.color = '';
                }, 500);
            }
        }, stepDuration);
    }

    getCSRFToken() {
        const csrfMeta = document.querySelector('meta[name=csrf-token]');
        if (csrfMeta) return csrfMeta.getAttribute('content');

        const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');
        if (csrfInput) return csrfInput.value;

        const csrfCookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));

        return csrfCookie ? csrfCookie.split('=')[1] : '';
    }
}

// Enhanced sync function for backward compatibility
window.syncWithEuropeanSMP = function () {
    const dashboard = window.smpDashboard;
    if (dashboard) {
        const syncButton = document.querySelector('.sync-btn');
        if (syncButton) {
            dashboard.handleEuropeanSMPSync({ target: syncButton, preventDefault: () => { } });
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.smpDashboard = new SMPDashboard();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SMPDashboard;
}
