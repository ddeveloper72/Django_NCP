/**
 * Base JavaScript functionality for EU NCP Portal
 * Handles tab functionality, mobile navigation, and core interactions
 */

// Tab functionality for Bootstrap-style tabs
function initializeTabs() {
  // Handle tab clicks - ONLY target main patient tabs, not extended patient tabs
  document.querySelectorAll('#patientTabs [data-bs-toggle="tab"]').forEach(function (tab) {
    tab.addEventListener('click', function (e) {
      e.preventDefault();
      console.log('Tab clicked:', this.getAttribute('data-bs-target'));

      // Remove active class from tabs and panes - ONLY in main patient tabs container
      const mainTabContainer = document.querySelector('#patientTabs');
      if (mainTabContainer) {
        mainTabContainer.querySelectorAll('.nav-link').forEach(function (link) {
          link.classList.remove('active');
        });
      }

      // Remove active from main tab content panes - ONLY target direct children
      const mainTabContent = document.querySelector('#patientTabContent');
      if (mainTabContent) {
        mainTabContent.querySelectorAll('.tab-pane').forEach(function (pane) {
          pane.classList.remove('show', 'active');
        });
      }

      // Add active class to clicked tab
      this.classList.add('active');
      console.log('Tab set to active:', this.id);

      // Show corresponding tab pane
      const targetId = this.getAttribute('data-bs-target');
      const targetPane = document.querySelector(targetId);
      if (targetPane) {
        targetPane.classList.add('show', 'active');
        console.log('Tab pane activated:', targetId);
      } else {
        console.error('Tab pane not found:', targetId);
      }
    });
  });
}

// Mobile navigation functionality
function initializeMobileNavigation() {
  const navbarToggle = document.querySelector('.navbar-toggle');
  const navbarNav = document.querySelector('.navbar-nav');

  if (!navbarToggle || !navbarNav) {
    return;
  }

  // Toggle mobile menu
  navbarToggle.addEventListener('click', function () {
    navbarNav.classList.toggle('navbar-nav-open');
    navbarToggle.classList.toggle('navbar-toggle-active');

    const isOpen = navbarNav.classList.contains('navbar-nav-open');
    navbarToggle.setAttribute('aria-expanded', isOpen);
  });

  // Close mobile menu when clicking outside
  document.addEventListener('click', function (event) {
    if (!event.target.closest('.navbar-main')) {
      navbarNav.classList.remove('navbar-nav-open');
      navbarToggle.classList.remove('navbar-toggle-active');
      navbarToggle.setAttribute('aria-expanded', 'false');
    }
  });

  // Close mobile menu on window resize
  window.addEventListener('resize', function () {
    if (window.innerWidth > 768) {
      navbarNav.classList.remove('navbar-nav-open');
      navbarToggle.classList.remove('navbar-toggle-active');
      navbarToggle.setAttribute('aria-expanded', 'false');
    }
  });

  // Set initial ARIA attributes
  navbarToggle.setAttribute('aria-expanded', 'false');
  navbarToggle.setAttribute('aria-controls', 'navbar-nav');
}

// Initialize all functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
  initializeTabs();
  initializeMobileNavigation();

  console.log('EU NCP Portal base functionality initialized');
});
