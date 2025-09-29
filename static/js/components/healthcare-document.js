/**
 * Healthcare Document Display JavaScript
 * Follows Django NCP Frontend Structure Compliance
 * External JavaScript for healthcare document interaction
 */

(function () {
    'use strict';

    // Healthcare Document Controller
    class HealthcareDocumentController {
        constructor() {
            this.init();
        }

        init() {
            this.setupAccordionBehavior();
            this.setupKeyboardNavigation();
            this.logDocumentInfo();
        }

        /**
         * Enhance accordion behavior with icon rotation
         */
        setupAccordionBehavior() {
            const accordionButtons = document.querySelectorAll('[data-bs-toggle="collapse"]');

            accordionButtons.forEach(button => {
                button.addEventListener('click', (event) => {
                    const chevron = button.querySelector('.icon');
                    if (chevron) {
                        // Use setTimeout to allow Bootstrap's state change to complete
                        setTimeout(() => {
                            const isExpanded = button.getAttribute('aria-expanded') === 'true';
                            chevron.className = isExpanded ?
                                'bi bi-chevron-down icon' :
                                'bi bi-chevron-right icon';
                        }, 50);
                    }
                });

                // Handle keyboard navigation
                button.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        button.click();
                    }
                });
            });
        }

        /**
         * Setup keyboard navigation for accessibility
         */
        setupKeyboardNavigation() {
            // Add keyboard support for print button
            const printButton = document.querySelector('[onclick*="print"]');
            if (printButton) {
                printButton.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        window.print();
                    }
                });
            }

            // Focus management for accordion sections
            document.addEventListener('keydown', (event) => {
                if (event.key === 'Tab') {
                    this.handleTabNavigation(event);
                }
            });
        }

        /**
         * Handle tab navigation for better accessibility
         */
        handleTabNavigation(event) {
            const focusableElements = document.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (event.shiftKey) {
                if (document.activeElement === firstElement) {
                    event.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    event.preventDefault();
                    firstElement.focus();
                }
            }
        }

        /**
         * Log document information for debugging
         */
        logDocumentInfo() {
            const documentData = this.extractDocumentData();

            console.log('Healthcare Document Loaded:', {
                patient_id: documentData.patientId,
                document_type: documentData.documentType,
                sections: documentData.sectionsCount,
                extraction_time: documentData.extractionTime,
                accessibility_features: this.checkAccessibilityFeatures()
            });
        }

        /**
         * Extract document data from DOM
         */
        extractDocumentData() {
            return {
                patientId: document.querySelector('.patient-id')?.textContent?.trim() || 'Unknown',
                documentType: document.querySelector('.status-badge')?.textContent?.trim() || 'Unknown',
                sectionsCount: document.querySelectorAll('.clinical-section').length,
                extractionTime: document.querySelector('.document-header__meta--secondary')?.textContent?.trim() || 'Unknown'
            };
        }

        /**
         * Check accessibility features implementation
         */
        checkAccessibilityFeatures() {
            const features = {
                aria_labels: document.querySelectorAll('[aria-label], [aria-labelledby]').length > 0,
                focus_management: document.querySelectorAll('[tabindex]').length > 0,
                semantic_markup: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length > 0,
                keyboard_navigation: document.querySelectorAll('[data-bs-toggle]').length > 0
            };

            return features;
        }
    }

    // Print functionality
    class PrintManager {
        static setupPrintStyles() {
            // Ensure all collapsed sections are shown when printing
            const mediaQuery = window.matchMedia('print');

            mediaQuery.addEventListener('change', (event) => {
                if (event.matches) {
                    // Before printing - expand all sections
                    document.querySelectorAll('.collapse:not(.show)').forEach(collapse => {
                        collapse.classList.add('show');
                    });
                } else {
                    // After printing - restore original state
                    // This is handled by the accordion component itself
                }
            });
        }
    }

    // Error handling
    class ErrorHandler {
        static handleErrors() {
            window.addEventListener('error', (event) => {
                console.error('Healthcare Document Error:', {
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno
                });
            });
        }
    }

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function () {
        // Initialize main controller
        const healthcareDoc = new HealthcareDocumentController();

        // Setup additional features
        PrintManager.setupPrintStyles();
        ErrorHandler.handleErrors();

        // Mark as initialized
        document.body.classList.add('healthcare-doc-initialized');

        // Dispatch custom event for other scripts
        document.dispatchEvent(new CustomEvent('healthcareDocumentReady', {
            detail: {
                controller: healthcareDoc,
                timestamp: new Date().toISOString()
            }
        }));
    });

})();
