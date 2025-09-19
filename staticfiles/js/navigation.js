/**
 * Navigation JavaScript
 * Handles mobile menu toggle functionality
 */

document.addEventListener('DOMContentLoaded', function () {
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarNav = document.querySelector('.navbar-nav');

    if (navbarToggle && navbarNav) {
        navbarToggle.addEventListener('click', function () {
            // Toggle the mobile menu
            navbarNav.classList.toggle('navbar-nav-open');
            navbarToggle.classList.toggle('navbar-toggle-active');

            // Update aria attributes for accessibility
            const isOpen = navbarNav.classList.contains('navbar-nav-open');
            navbarToggle.setAttribute('aria-expanded', isOpen);
            navbarToggle.setAttribute('aria-label', isOpen ? 'Close menu' : 'Open menu');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', function (event) {
            if (!event.target.closest('.navbar-main')) {
                navbarNav.classList.remove('navbar-nav-open');
                navbarToggle.classList.remove('navbar-toggle-active');
                navbarToggle.setAttribute('aria-expanded', 'false');
                navbarToggle.setAttribute('aria-label', 'Open menu');
            }
        });

        // Close mobile menu when window is resized to desktop
        window.addEventListener('resize', function () {
            if (window.innerWidth > 768) { // Assuming 768px is the mobile breakpoint
                navbarNav.classList.remove('navbar-nav-open');
                navbarToggle.classList.remove('navbar-toggle-active');
                navbarToggle.setAttribute('aria-expanded', 'false');
                navbarToggle.setAttribute('aria-label', 'Open menu');
            }
        });

        // Initialize aria attributes
        navbarToggle.setAttribute('aria-expanded', 'false');
        navbarToggle.setAttribute('aria-label', 'Open menu');
        navbarToggle.setAttribute('aria-controls', 'navbar-nav');
    }
});
