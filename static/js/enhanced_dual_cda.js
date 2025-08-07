/**
 * Enhanced Dual Language CDA Display JavaScript
 * Provides interactive functionality for dual language display and responsive tables
 */

class DualLanguageDisplay {
    constructor(options) {
        this.config = {
            sourceLanguage: options.sourceLanguage || 'en',
            targetLanguage: options.targetLanguage || 'en',
            medicationFields: options.medicationFields || {},
            responsiveConfig: options.responsiveConfig || {},
            currentMode: 'dual' // dual, original, translated
        };

        this.breakpoints = {
            mobile: 600,
            tablet: 900,
            desktop: 1200
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupResponsiveTable();
        this.setupLanguageControls();
        this.setupMobileDetection();

        console.log('✅ Dual Language Display initialized');
    }

    setupEventListeners() {
        // Language display mode controls
        document.addEventListener('change', (e) => {
            if (e.target.matches('input[name^="lang-mode-"]')) {
                this.handleLanguageModeChange(e);
            }
        });

        // Global language display mode
        const globalLanguageSelect = document.getElementById('language-display-mode');
        if (globalLanguageSelect) {
            globalLanguageSelect.addEventListener('change', (e) => {
                this.setGlobalLanguageMode(e.target.value);
            });
        }

        // Mobile view toggle
        const mobileToggle = document.getElementById('toggle-mobile-view');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => {
                this.toggleMobileView();
            });
        }

        // Column controls
        document.addEventListener('click', (e) => {
            if (e.target.matches('[id^="toggle-columns-"]')) {
                this.toggleColumnControls(e.target);
            }

            if (e.target.matches('[id^="mobile-view-"]')) {
                this.toggleSectionMobileView(e.target);
            }
        });

        // Expandable details
        document.addEventListener('click', (e) => {
            if (e.target.closest('.expand-details')) {
                this.handleDetailsExpansion(e);
            }
        });

        // Floating controls
        this.setupFloatingControls();

        // Window resize handling
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    setupResponsiveTable() {
        this.checkTableOverflow();
        this.setupStickyHeaders();
        this.updateResponsiveColumns();
    }

    setupLanguageControls() {
        // Initialize all tables with dual language mode
        const tables = document.querySelectorAll('.medication-table-enhanced');
        tables.forEach(table => {
            table.setAttribute('data-language-mode', 'dual');
        });
    }

    setupMobileDetection() {
        this.isMobile = window.innerWidth <= this.breakpoints.mobile;
        this.isTablet = window.innerWidth <= this.breakpoints.tablet;

        if (this.isMobile) {
            this.showFloatingControls();
            this.autoSwitchToMobileCards();
        }
    }

    handleLanguageModeChange(event) {
        const mode = event.target.value;
        const sectionCode = event.target.name.replace('lang-mode-', '');
        const table = document.querySelector(`[data-section-code="${sectionCode}"]`);

        if (table) {
            table.setAttribute('data-language-mode', mode);
            this.updateTableDisplay(table, mode);
        }
    }

    setGlobalLanguageMode(mode) {
        this.config.currentMode = mode;

        // Update all tables
        const tables = document.querySelectorAll('.medication-table-enhanced');
        tables.forEach(table => {
            table.setAttribute('data-language-mode', mode);
            this.updateTableDisplay(table, mode);
        });

        // Update all radio buttons
        const radioButtons = document.querySelectorAll('input[name^="lang-mode-"]');
        radioButtons.forEach(radio => {
            if (radio.value === mode) {
                radio.checked = true;
            }
        });

        console.log(`🌐 Global language mode set to: ${mode}`);
    }

    updateTableDisplay(table, mode) {
        // Update table data attribute
        table.setAttribute('data-language-mode', mode);

        // Update corresponding mobile cards if they exist
        const sectionCode = table.getAttribute('data-section-code');
        const mobileCards = document.getElementById(`mobile-cards-${sectionCode}`);

        if (mobileCards) {
            mobileCards.setAttribute('data-language-mode', mode);
        }

        // Trigger any custom events
        table.dispatchEvent(new CustomEvent('languageModeChanged', {
            detail: { mode, sectionCode }
        }));
    }

    toggleMobileView() {
        const container = document.getElementById('sections-container');
        const isCurrentlyMobile = container.classList.contains('mobile-view-active');

        if (isCurrentlyMobile) {
            this.showTableView();
        } else {
            this.showMobileCardsView();
        }
    }

    showTableView() {
        const container = document.getElementById('sections-container');
        container.classList.remove('mobile-view-active');

        // Show all table containers
        document.querySelectorAll('.table-container-responsive').forEach(table => {
            table.style.display = 'block';
        });

        // Hide all mobile card containers
        document.querySelectorAll('.mobile-cards-container').forEach(cards => {
            cards.style.display = 'none';
        });

        // Update button text
        const button = document.getElementById('toggle-mobile-view');
        if (button) {
            button.textContent = '📱 Mobile View';
        }

        console.log('📊 Switched to table view');
    }

    showMobileCardsView() {
        const container = document.getElementById('sections-container');
        container.classList.add('mobile-view-active');

        // Hide all table containers
        document.querySelectorAll('.table-container-responsive').forEach(table => {
            table.style.display = 'none';
        });

        // Show all mobile card containers
        document.querySelectorAll('.mobile-cards-container').forEach(cards => {
            cards.style.display = 'block';
        });

        // Update button text
        const button = document.getElementById('toggle-mobile-view');
        if (button) {
            button.textContent = '📊 Table View';
        }

        console.log('📱 Switched to mobile cards view');
    }

    toggleSectionMobileView(button) {
        const sectionCode = button.id.replace('mobile-view-', '');
        const tableContainer = document.getElementById(`table-container-${sectionCode}`);
        const mobileCards = document.getElementById(`mobile-cards-${sectionCode}`);

        if (tableContainer && mobileCards) {
            const isShowingTable = tableContainer.style.display !== 'none';

            if (isShowingTable) {
                tableContainer.style.display = 'none';
                mobileCards.style.display = 'block';
                button.textContent = '📊 Table';
            } else {
                tableContainer.style.display = 'block';
                mobileCards.style.display = 'none';
                button.textContent = '📱 Cards';
            }
        }
    }

    toggleColumnControls(button) {
        const sectionCode = button.id.replace('toggle-columns-', '');

        // Create column visibility modal/dropdown
        this.showColumnVisibilityControls(sectionCode);
    }

    showColumnVisibilityControls(sectionCode) {
        const table = document.querySelector(`#medication-table-${sectionCode}`);
        if (!table) return;

        // Get all columns
        const headers = table.querySelectorAll('th[data-field]');
        const modalHtml = this.generateColumnControlModal(sectionCode, headers);

        // Show modal or dropdown
        this.showModal('Column Visibility', modalHtml);
    }

    generateColumnControlModal(sectionCode, headers) {
        let html = '<div class="column-controls-modal">';
        html += '<p>Select which columns to display:</p>';
        html += '<div class="column-checkboxes">';

        headers.forEach((header, index) => {
            const field = header.getAttribute('data-field');
            const priority = header.classList.contains('priority-1') ? 1 :
                header.classList.contains('priority-2') ? 2 : 3;
            const isVisible = !header.style.display || header.style.display !== 'none';

            html += `
                <label class="column-checkbox">
                    <input type="checkbox" 
                           value="${field}" 
                           ${isVisible ? 'checked' : ''}
                           data-section="${sectionCode}"
                           data-priority="${priority}">
                    <span class="priority-${priority}">${header.textContent.trim()}</span>
                    <small class="priority-indicator">Priority ${priority}</small>
                </label>
            `;
        });

        html += '</div>';
        html += '<div class="modal-actions">';
        html += '<button class="btn btn-sm btn-outline-secondary" onclick="dualLanguageDisplay.resetColumns(\'' + sectionCode + '\')">Reset</button>';
        html += '<button class="btn btn-sm btn-primary" onclick="dualLanguageDisplay.applyColumnChanges(\'' + sectionCode + '\')">Apply</button>';
        html += '</div>';
        html += '</div>';

        return html;
    }

    resetColumns(sectionCode) {
        // Reset to default responsive behavior
        const table = document.querySelector(`#medication-table-${sectionCode}`);
        if (table) {
            const headers = table.querySelectorAll('th[data-field]');
            const cells = table.querySelectorAll('td[data-field]');

            // Show all columns
            headers.forEach(header => {
                header.style.display = '';
            });
            cells.forEach(cell => {
                cell.style.display = '';
            });

            // Reapply responsive classes
            this.updateResponsiveColumns();
        }

        this.closeModal();
    }

    applyColumnChanges(sectionCode) {
        const checkboxes = document.querySelectorAll(`input[data-section="${sectionCode}"]`);
        const table = document.querySelector(`#medication-table-${sectionCode}`);

        if (table) {
            checkboxes.forEach(checkbox => {
                const field = checkbox.value;
                const isVisible = checkbox.checked;

                const headers = table.querySelectorAll(`th[data-field="${field}"]`);
                const cells = table.querySelectorAll(`td[data-field="${field}"]`);

                headers.forEach(header => {
                    header.style.display = isVisible ? '' : 'none';
                });
                cells.forEach(cell => {
                    cell.style.display = isVisible ? '' : 'none';
                });
            });
        }

        this.closeModal();
    }

    handleDetailsExpansion(event) {
        const button = event.target.closest('.expand-details');
        const icon = button.querySelector('i');

        // Toggle icon rotation
        if (button.getAttribute('aria-expanded') === 'true') {
            icon.style.transform = 'rotate(180deg)';
        } else {
            icon.style.transform = 'rotate(0deg)';
        }
    }

    setupFloatingControls() {
        const floatingControls = document.getElementById('floating-controls');
        if (!floatingControls) return;

        // Show all columns button
        const showAllBtn = document.getElementById('show-all-columns');
        if (showAllBtn) {
            showAllBtn.addEventListener('click', () => {
                this.showAllColumns();
            });
        }

        // Priority view button
        const priorityBtn = document.getElementById('priority-view');
        if (priorityBtn) {
            priorityBtn.addEventListener('click', () => {
                this.setPriorityView();
            });
        }

        // Mobile cards button
        const mobileCardsBtn = document.getElementById('mobile-cards');
        if (mobileCardsBtn) {
            mobileCardsBtn.addEventListener('click', () => {
                this.showMobileCardsView();
            });
        }
    }

    showAllColumns() {
        document.querySelectorAll('.medication-table th, .medication-table td').forEach(element => {
            element.style.display = '';
        });

        console.log('📊 All columns displayed');
    }

    setPriorityView() {
        // Show only priority 1 columns
        document.querySelectorAll('.priority-2, .priority-3').forEach(element => {
            element.style.display = 'none';
        });

        document.querySelectorAll('.priority-1').forEach(element => {
            element.style.display = '';
        });

        console.log('🎯 Priority view activated');
    }

    checkTableOverflow() {
        const tableContainers = document.querySelectorAll('.table-container-responsive');

        tableContainers.forEach(container => {
            const table = container.querySelector('table');
            if (table && table.scrollWidth > container.clientWidth) {
                container.classList.add('has-horizontal-scroll');
                this.showScrollIndicator(container);
            }
        });
    }

    showScrollIndicator(container) {
        if (!container.querySelector('.scroll-indicator')) {
            const indicator = document.createElement('div');
            indicator.className = 'scroll-indicator';
            indicator.innerHTML = '← Scroll to see more columns →';
            container.appendChild(indicator);
        }
    }

    setupStickyHeaders() {
        // Enhanced sticky header handling for medication tables
        const tables = document.querySelectorAll('.medication-table');

        tables.forEach(table => {
            const thead = table.querySelector('thead');
            if (thead) {
                thead.style.position = 'sticky';
                thead.style.top = '0';
                thead.style.zIndex = '100';
            }
        });
    }

    updateResponsiveColumns() {
        const width = window.innerWidth;

        // Apply responsive rules based on current viewport
        if (width <= this.breakpoints.tablet) {
            document.querySelectorAll('.priority-3').forEach(el => {
                el.style.display = 'none';
            });
        }

        if (width <= this.breakpoints.mobile) {
            document.querySelectorAll('.priority-2').forEach(el => {
                el.style.display = 'none';
            });
        }

        if (width > this.breakpoints.tablet) {
            document.querySelectorAll('.priority-2, .priority-3').forEach(el => {
                if (!el.style.display || el.style.display === 'none') {
                    el.style.display = '';
                }
            });
        }
    }

    autoSwitchToMobileCards() {
        if (this.isMobile) {
            this.showMobileCardsView();
        }
    }

    showFloatingControls() {
        const controls = document.getElementById('floating-controls');
        if (controls) {
            controls.style.display = 'flex';
        }
    }

    hideFloatingControls() {
        const controls = document.getElementById('floating-controls');
        if (controls) {
            controls.style.display = 'none';
        }
    }

    handleResize() {
        const newWidth = window.innerWidth;
        const wasTablet = this.isTablet;
        const wasMobile = this.isMobile;

        this.isTablet = newWidth <= this.breakpoints.tablet;
        this.isMobile = newWidth <= this.breakpoints.mobile;

        // Update responsive columns
        this.updateResponsiveColumns();

        // Handle mobile/desktop transitions
        if (!wasMobile && this.isMobile) {
            this.showFloatingControls();
        } else if (wasMobile && !this.isMobile) {
            this.hideFloatingControls();
            this.showTableView();
        }

        // Update table overflow indicators
        this.checkTableOverflow();
    }

    showModal(title, content) {
        // Simple modal implementation
        const modal = document.createElement('div');
        modal.className = 'dual-lang-modal';
        modal.innerHTML = `
            <div class="modal-backdrop" onclick="dualLanguageDisplay.closeModal()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h5>${title}</h5>
                    <button class="close-btn" onclick="dualLanguageDisplay.closeModal()">×</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    closeModal() {
        const modal = document.querySelector('.dual-lang-modal');
        if (modal) {
            modal.remove();
        }
    }
}

// Initialize when DOM is ready
let dualLanguageDisplay;

document.addEventListener('DOMContentLoaded', function () {
    // Will be initialized by the main page with configuration
    console.log('🎯 Dual Language Display ready for initialization');
});

// Export for global access
window.DualLanguageDisplay = DualLanguageDisplay;
