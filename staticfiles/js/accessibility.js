/**
 * Accessibility Enhancement Module for EU NCP Portal
 * Ensures WCAG 2.1 AA compliance and improved user experience
 */

class AccessibilityManager {
  constructor() {
    this.init();
  }

  init() {
    this.addSkipLinks();
    this.enhanceKeyboardNavigation();
    this.addAriaLabels();
    this.implementFocusManagement();
    this.addHighContrastMode();
    this.setupReducedMotion();
    this.addLanguageSupport();

    console.log('Accessibility enhancements initialized');
  }

  // Add skip links for keyboard navigation
  addSkipLinks() {
    // Don't add skip links if navigation is visible (has navbar) or skip links already exist
    if (document.querySelector('.skip-links') || document.querySelector('#main-navigation')) {
      return;
    }

    const skipLinks = document.createElement('div');
    skipLinks.className = 'skip-links';
    skipLinks.innerHTML = `
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#main-navigation" class="skip-link">Skip to navigation</a>
            <a href="#search" class="skip-link">Skip to search</a>
        `;

    document.body.insertBefore(skipLinks, document.body.firstChild);

    // Add CSS for skip links
    if (!document.querySelector('#skip-links-css')) {
      const style = document.createElement('style');
      style.id = 'skip-links-css';
      style.textContent = `
                .skip-links {
                    position: absolute;
                    top: -100px;
                    left: 6px;
                    z-index: 9999;
                }
                .skip-link {
                    position: absolute;
                    top: -100px;
                    left: 0;
                    padding: 8px 12px;
                    background-color: #005eb8;
                    color: white;
                    text-decoration: none;
                    border-radius: 0 0 4px 4px;
                    font-weight: bold;
                    font-size: 14px;
                    transition: top 0.2s ease;
                    white-space: nowrap;
                }
                .skip-link:focus {
                    top: 0;
                    outline: 3px solid #ff6900;
                    outline-offset: 2px;
                    z-index: 999999;
                }
            `;
      document.head.appendChild(style);
    }
  }

  // Enhance keyboard navigation
  enhanceKeyboardNavigation() {
    // Add visible focus indicators
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.add('user-is-tabbing');
      }
    });

    document.addEventListener('mousedown', () => {
      document.body.classList.remove('user-is-tabbing');
    });

    // Enhance dropdown navigation
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(dropdown => {
      dropdown.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          dropdown.click();
        }
      });
    });

    // Trap focus in modals
    this.setupModalFocusTrap();
  }

  // Add comprehensive ARIA labels
  addAriaLabels() {
    // Enhance form inputs
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      if (!input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label) {
          input.setAttribute('aria-labelledby', label.id || this.generateId('label'));
          if (!label.id) label.id = input.getAttribute('aria-labelledby');
        }
      }

      // Add required indicators
      if (input.hasAttribute('required')) {
        input.setAttribute('aria-required', 'true');
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label && !label.textContent.includes('*')) {
          label.innerHTML += ' <span class="required-indicator" aria-label="required">*</span>';
        }
      }
    });

    // Enhance buttons
    const buttons = document.querySelectorAll('button:not([aria-label])');
    buttons.forEach(button => {
      if (!button.textContent.trim()) {
        const icon = button.querySelector('i, svg');
        if (icon) {
          button.setAttribute('aria-label', this.getButtonAriaLabel(button));
        }
      }
    });

    // Enhance tables
    const tables = document.querySelectorAll('table:not([role])');
    tables.forEach(table => {
      table.setAttribute('role', 'table');
      const caption = table.querySelector('caption');
      if (!caption) {
        const tableCaption = document.createElement('caption');
        tableCaption.className = 'sr-only';
        tableCaption.textContent = 'Data table';
        table.insertBefore(tableCaption, table.firstChild);
      }
    });

    // Enhance navigation landmarks
    const nav = document.querySelector('nav:not([aria-label])');
    if (nav) nav.setAttribute('aria-label', 'Main navigation');

    const main = document.querySelector('main');
    if (main) main.setAttribute('aria-label', 'Main content');
  }

  // Implement focus management
  implementFocusManagement() {
    // Store and restore focus for single-page app navigation
    let lastFocusedElement = null;

    document.addEventListener('focusin', (e) => {
      lastFocusedElement = e.target;
    });

    // Enhance tab panels
    const tabPanels = document.querySelectorAll('[role="tabpanel"]');
    tabPanels.forEach(panel => {
      if (!panel.hasAttribute('tabindex')) {
        panel.setAttribute('tabindex', '0');
      }
    });

    // Add focus indicators for custom elements
    const customFocusElements = document.querySelectorAll('.card, .list-group-item');
    customFocusElements.forEach(element => {
      if (!element.hasAttribute('tabindex') && element.hasAttribute('data-href')) {
        element.setAttribute('tabindex', '0');
        element.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            window.location.href = element.dataset.href;
          }
        });
      }
    });
  }

  // Add high contrast mode toggle
  addHighContrastMode() {
    const contrastToggle = document.createElement('button');
    contrastToggle.id = 'contrast-toggle';
    contrastToggle.className = 'btn btn-outline-secondary btn-sm position-fixed';
    contrastToggle.style.cssText = 'top: 10px; right: 10px; z-index: 1050;';
    contrastToggle.innerHTML = '<i class="fas fa-adjust" aria-hidden="true"></i>';
    contrastToggle.setAttribute('aria-label', 'Toggle high contrast mode');
    contrastToggle.setAttribute('title', 'Toggle high contrast mode');

    contrastToggle.addEventListener('click', () => {
      document.body.classList.toggle('high-contrast');
      const isHighContrast = document.body.classList.contains('high-contrast');
      localStorage.setItem('highContrast', isHighContrast);
    });

    document.body.appendChild(contrastToggle);

    // Restore high contrast setting
    if (localStorage.getItem('highContrast') === 'true') {
      document.body.classList.add('high-contrast');
    }

    // Add high contrast CSS
    if (!document.querySelector('#high-contrast-css')) {
      const style = document.createElement('style');
      style.id = 'high-contrast-css';
      style.textContent = `
                .user-is-tabbing *:focus {
                    outline: 3px solid #ff6900 !important;
                    outline-offset: 2px !important;
                }
            `;
      document.head.appendChild(style);
    }
  }

  // Setup reduced motion preferences
  setupReducedMotion() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.documentElement.style.setProperty('--animation-duration', '0.01ms');
      document.documentElement.style.setProperty('--transition-duration', '0.01ms');

      // Disable auto-playing animations
      const animations = document.querySelectorAll('[data-auto-animate]');
      animations.forEach(element => {
        element.style.animationPlayState = 'paused';
      });
    }
  }

  // Setup modal focus trapping
  setupModalFocusTrap() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
      modal.addEventListener('shown.bs.modal', () => {
        this.trapFocus(modal);
      });
    });
  }

  // Trap focus within an element
  trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    element.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    });

    firstElement.focus();
  }

  // Add language support
  addLanguageSupport() {
    document.documentElement.setAttribute('lang', 'en');

    // Add lang attributes to content sections
    const languageSections = document.querySelectorAll('[data-lang]');
    languageSections.forEach(section => {
      section.setAttribute('lang', section.dataset.lang);
    });
  }

  // Generate unique ID
  generateId(prefix = 'element') {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Get appropriate ARIA label for buttons
  getButtonAriaLabel(button) {
    const icon = button.querySelector('i');
    if (icon) {
      if (icon.classList.contains('fa-search')) return 'Search';
      if (icon.classList.contains('fa-edit')) return 'Edit';
      if (icon.classList.contains('fa-delete') || icon.classList.contains('fa-trash')) return 'Delete';
      if (icon.classList.contains('fa-save')) return 'Save';
      if (icon.classList.contains('fa-close') || icon.classList.contains('fa-times')) return 'Close';
      if (icon.classList.contains('fa-plus')) return 'Add';
      if (icon.classList.contains('fa-download')) return 'Download';
      if (icon.classList.contains('fa-print')) return 'Print';
    }
    return 'Action button';
  }
}

// Image lazy loading implementation
class LazyImageLoader {
  constructor() {
    this.images = document.querySelectorAll('img[data-src]');
    this.imageObserver = null;
    this.init();
  }

  init() {
    if ('IntersectionObserver' in window) {
      this.imageObserver = new IntersectionObserver(this.onIntersection.bind(this));
      this.images.forEach(img => this.imageObserver.observe(img));
    } else {
      // Fallback for older browsers
      this.loadAllImages();
    }
  }

  onIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        this.loadImage(entry.target);
        this.imageObserver.unobserve(entry.target);
      }
    });
  }

  loadImage(img) {
    img.src = img.dataset.src;
    img.classList.add('loaded');

    // Add alt text if missing
    if (!img.alt) {
      img.alt = 'Healthcare related image';
    }

    img.addEventListener('load', () => {
      img.classList.add('fade-in');
    });
  }

  loadAllImages() {
    this.images.forEach(img => this.loadImage(img));
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new AccessibilityManager();
  new LazyImageLoader();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AccessibilityManager, LazyImageLoader };
}
