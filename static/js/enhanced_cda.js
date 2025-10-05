// ============================================================================
// ENHANCED CDA DISPLAY FUNCTIONALITY
// ============================================================================
// JavaScript for Enhanced CDA patient display templates
// Handles Bootstrap tabs, extended patient sections, and interactive elements

/**
 * Initialize Enhanced CDA functionality
 * Called when DOM is ready
 */
function initializeEnhancedCDA() {
  console.log('🚀 ENHANCED CDA INITIALIZING - DEBUG VERSION');
  console.log('🚀 DOM READY - Starting enhanced CDA initialization');

  // Check if the container exists
  const extendedContainer = document.querySelector('#extendedPatientSection');
  console.log('🔍 Extended container found:', extendedContainer ? 'YES' : 'NO');
  if (extendedContainer) {
    console.log('🔍 Container ID:', extendedContainer.id);
    console.log('🔍 Container classes:', extendedContainer.className);
  }

  // Check for tab buttons
  const tabButtons = document.querySelectorAll('[data-action="show-extended-tab"]');
  console.log('🔍 Tab buttons found:', tabButtons.length);
  tabButtons.forEach((btn, index) => {
    console.log(`🔍 Button ${index}:`, btn.dataset.tabType, btn.textContent.trim());
  });

  // Check for tab content elements
  const tabContents = document.querySelectorAll('.clinical-tab-content');
  console.log('🔍 Tab contents found:', tabContents.length);
  tabContents.forEach((content, index) => {
    console.log(`🔍 Content ${index}:`, content.id, content.classList.contains('active') ? 'ACTIVE' : 'INACTIVE');
  });

  console.log('Initializing Bootstrap tabs...');

  // Initialize Bootstrap tabs for Extended Patient Info
  const extendedInfoTabs = document.querySelectorAll('#extendedInfoTabs button[data-bs-toggle="tab"]');
  extendedInfoTabs.forEach(tab => {
    new bootstrap.Tab(tab);
  });

  // Initialize Bootstrap tabs for Clinical Sections
  const clinicalTabs = document.querySelectorAll('.clinical-tabs button[data-bs-toggle="tab"]');
  clinicalTabs.forEach(tab => {
    new bootstrap.Tab(tab);
  });

  // Initialize pregnancy history tabs
  initializePregnancyHistoryTabs();

  // Enhanced hover effects for interactive elements
  const cards = document.querySelectorAll('.card');
  cards.forEach(card => {
    card.addEventListener('mouseenter', function () {
      this.style.transform = 'translateY(-2px)';
      this.style.transition = 'transform 0.2s ease';
    });

    card.addEventListener('mouseleave', function () {
      this.style.transform = 'translateY(0)';
    });
  });

  // Initialize Bootstrap tooltips
  initializeTooltips();

  // Initialize Extended Patient Event Delegation
  initializeExtendedPatientEventDelegation();

  // Show Personal Information tab by default
  setTimeout(() => {
    const personalTab = document.getElementById('extended_patient_personal');
    if (personalTab) {
      showExtendedTab('extended_patient', 'personal');
    }
  }, 100); // Small delay to ensure DOM is ready

  // Initialize pregnancy history tabs
  initializePregnancyHistoryTabs();

  console.log('Bootstrap functionality initialized');
}

/**
 * Extended Patient Tab Management Function - SIMPLIFIED DEBUG VERSION
 * @param {string} sectionId - ID of the section containing tabs
 * @param {string} tabType - Type of tab to show (personal, healthcare, system, clinical, orcd)
 */
function showExtendedTab(sectionId, tabType) {
  // Get all tab content elements
  const personalTab = document.getElementById(sectionId + '_personal');
  const healthcareTab = document.getElementById(sectionId + '_healthcare');
  const systemTab = document.getElementById(sectionId + '_system');
  const clinicalTab = document.getElementById(sectionId + '_clinical');
  const pdfsTab = document.getElementById(sectionId + '_pdfs');

  const allTabs = [personalTab, healthcareTab, systemTab, clinicalTab, pdfsTab].filter(tab => tab !== null);

  // Remove active class from ALL tabs
  allTabs.forEach(tab => {
    if (tab) {
      tab.classList.remove('active');
    }
  });

  // Add active class to the selected tab
  let activeTab = null;

  if (tabType === 'personal' && personalTab) {
    activeTab = personalTab;
  } else if (tabType === 'healthcare' && healthcareTab) {
    activeTab = healthcareTab;
  } else if (tabType === 'system' && systemTab) {
    activeTab = systemTab;
  } else if (tabType === 'clinical' && clinicalTab) {
    activeTab = clinicalTab;
  } else if (tabType === 'pdfs' && pdfsTab) {
    activeTab = pdfsTab;
  }

  if (activeTab) {
    activeTab.classList.add('active');
    // Force refresh
    activeTab.offsetHeight;

    // Auto-show first OrCD when Original Clinical Documents tab is activated
    if (tabType === 'pdfs') {
      setTimeout(() => {
        const firstPdfViewer = activeTab.querySelector('[data-action="show-pdf-viewer"]');
        if (firstPdfViewer) {
          // Automatically show the first OrCD viewer
          const pdfIndex = firstPdfViewer.dataset.pdfIndex;
          console.log('Auto-loading OrCD viewer for index:', pdfIndex);

          // Find the OrCD viewer container and show it
          const viewerContainer = document.getElementById(`pdf-viewer-${pdfIndex}`);
          if (viewerContainer) {
            viewerContainer.classList.remove('hidden');

            // Update button to show "Hide" instead of "View"
            const buttonIcon = firstPdfViewer.querySelector('i');
            const buttonText = firstPdfViewer.childNodes[firstPdfViewer.childNodes.length - 1];
            if (buttonIcon && buttonText) {
              buttonIcon.className = 'fa-solid fa-eye-slash me-1';
              buttonText.textContent = 'Hide';
            }

            // Change button action to hide
            firstPdfViewer.dataset.action = 'hide-pdf-viewer';
          }
        }
      }, 200); // Small delay to ensure tab is fully rendered
    }
  }  // Update button states
  const container = activeTab ? activeTab.closest('.clinical-section') : document.querySelector('.clinical-section');
  if (container) {
    const buttons = container.querySelectorAll('.tab-navigation .tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));

    const tabTypeMap = { 'personal': 0, 'healthcare': 1, 'system': 2, 'clinical': 3, 'pdfs': 4 }; // pdfs = OrCD tab
    const buttonIndex = tabTypeMap[tabType];

    if (buttonIndex !== undefined && buttons[buttonIndex]) {
      buttons[buttonIndex].classList.add('active');
    }
  }
}

/**
 * Date formatting utility function for medical dates
 * @param {string} dateStr - Date string in various formats
 * @returns {string} Formatted date string
 */
function formatMedicalDate(dateStr) {
  if (!dateStr || typeof dateStr !== 'string') return dateStr;

  dateStr = dateStr.trim();
  let parsedDate = null;

  // Format: YYYYMMDDHHMMSS (e.g., 20130317124500)
  if (/^\d{14}$/.test(dateStr)) {
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    const hour = dateStr.substring(8, 10);
    const minute = dateStr.substring(10, 12);
    const second = dateStr.substring(12, 14);
    parsedDate = new Date(year, month - 1, day, hour, minute, second);
  }
  // Format: YYYYMMDD (e.g., 20130317)
  else if (/^\d{8}$/.test(dateStr)) {
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    parsedDate = new Date(year, month - 1, day);
  }
  // Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS (ISO format)
  else if (/^\d{4}-\d{2}-\d{2}/.test(dateStr)) {
    parsedDate = new Date(dateStr);
  }

  if (parsedDate && !isNaN(parsedDate.getTime())) {
    const month = String(parsedDate.getMonth() + 1).padStart(2, '0');
    const day = String(parsedDate.getDate()).padStart(2, '0');
    const year = parsedDate.getFullYear();
    const hour = String(parsedDate.getHours()).padStart(2, '0');
    const minute = String(parsedDate.getMinutes()).padStart(2, '0');

    if (/^\d{8}$/.test(dateStr.trim()) || /^\d{4}-\d{2}-\d{2}$/.test(dateStr.trim())) {
      return `${month}/${day}/${year}`;
    } else {
      return `${month}/${day}/${year} ${hour}:${minute}`;
    }
  }
  return dateStr;
}

/**
 * Initialize Bootstrap tooltips
 * Sets up tooltips for all elements with data-bs-toggle="tooltip"
 */
function initializeTooltips() {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

/**
 * Show clinical section tab (Structured Data vs Original Content) - Legacy function name
 * @param {string} sectionId - ID of the clinical section
 * @param {string} tabType - Type of tab to show ('structured' or 'original')
 */
function showTab(sectionId, tabType) {
  // Just call the main function to avoid code duplication
  showClinicalTab(sectionId, tabType);
}

/**
 * Show clinical section tab (Structured Data vs Original Content)
 * @param {string} sectionId - ID of the clinical section
 * @param {string} tabType - Type of tab to show ('structured' or 'original')
 */
function showClinicalTab(sectionId, tabType) {
  console.log('Switching clinical tab:', tabType);

  // Find the tab content elements
  const structuredTab = document.getElementById(sectionId + '_structured');
  const originalTab = document.getElementById(sectionId + '_original');

  console.log('Looking for elements:');
  console.log('- Structured tab:', sectionId + '_structured', '→', structuredTab);
  console.log('- Original tab:', sectionId + '_original', '→', originalTab);

  if (!structuredTab && !originalTab) {
    console.error('No clinical tab content found for:', sectionId);
    // Let's see what elements with similar IDs exist
    const similarElements = document.querySelectorAll('[id*="' + sectionId + '"]');
    console.log('Found similar elements:', similarElements);
    return;
  }

  // Find the tab buttons
  const container = (structuredTab || originalTab).closest('.card') || (structuredTab || originalTab).closest('.clinical-section');
  if (!container) {
    console.error('Clinical section container not found for:', sectionId);
    return;
  }

  const buttons = container.querySelectorAll('.tab-button');

  // Hide all tabs and remove active class from buttons
  if (structuredTab) structuredTab.classList.remove('active');
  if (originalTab) originalTab.classList.remove('active');
  buttons.forEach(btn => btn.classList.remove('active'));

  // Show selected tab and activate corresponding button
  if (tabType === 'structured' && structuredTab) {
    structuredTab.classList.add('active');
    if (buttons[0]) buttons[0].classList.add('active');
  } else if (tabType === 'original' && originalTab) {
    originalTab.classList.add('active');
    if (buttons[1]) buttons[1].classList.add('active');
  }
}

/**
 * Initialize event delegation for extended patient tabs
 * This handles the clicking of tab buttons that use data-action attributes
 */
function initializeExtendedPatientEventDelegation() {
  console.log('🔧 STARTING Event delegation setup...');

  const extendedContainer = document.querySelector('#extendedPatientSection');
  if (!extendedContainer) {
    console.error('❌ Extended patient container not found!');
    return;
  }

  console.log('✅ Extended patient container found:', extendedContainer.id);

  // Prevent duplicate listeners
  if (extendedContainer.dataset.initialized === 'true') {
    console.log('⚠️ Event delegation already initialized, skipping...');
    return;
  }

  console.log('🔧 Setting up click listener on container...');

  extendedContainer.addEventListener('click', function (event) {
    console.log('🎯 CLICK DETECTED! Target:', event.target.tagName, event.target.className);
    console.log('🎯 Click event target text:', event.target.textContent.trim());

    // Check if this is a Bootstrap accordion button - let Bootstrap handle it completely
    const clickedElement = event.target;
    const hasCollapseToggle = clickedElement.hasAttribute('data-bs-toggle') &&
      clickedElement.getAttribute('data-bs-toggle') === 'collapse';
    const hasCollapseTarget = clickedElement.hasAttribute('data-bs-target');
    const isAccordionButton = hasCollapseToggle || hasCollapseTarget ||
      clickedElement.closest('[data-bs-toggle="collapse"]') ||
      clickedElement.classList.contains('accordion-button');

    if (isAccordionButton) {
      console.log('🔧 Bootstrap accordion button detected - COMPLETELY bypassing our handler');
      return; // Do absolutely nothing - let Bootstrap handle it 100%
    }

    // Find the closest button with data-action (in case user clicks on icon or text inside button)
    const target = event.target.closest('[data-action]') || event.target;
    const action = target.dataset.action;

    console.log('🔧 Closest target with data-action:', target.tagName, target.className);
    console.log('🔧 Action found:', action);
    console.log('🔧 All target dataset:', target.dataset);

    // If we found a button with an action, prevent Bootstrap from interfering
    if (action) {
      console.log('✅ Action detected, preventing default behavior');
      event.preventDefault();
      event.stopPropagation();

      // Check if THIS SPECIFIC button is disabled
      if (target.disabled || target.dataset.disabled === 'true') {
        console.log('Button disabled:', action);
        return;
      }
    } else {
      console.log('🔧 No action found on target');
      return;
    }

    console.log('🎯 SWITCH STATEMENT - Action value:', JSON.stringify(action), 'Type:', typeof action);
    switch (action) {
      case 'show-extended-tab':
        const sectionId = target.dataset.sectionId;
        const tabType = target.dataset.tabType;
        console.log('🔧 Section ID:', sectionId);
        console.log('🔧 Tab Type:', tabType);
        console.log('🔧 All dataset:', target.dataset);
        console.log('Switching to tab:', tabType);
        if (sectionId && tabType) {
          showExtendedTab(sectionId, tabType);
        } else {
          console.error('❌ Missing sectionId or tabType', { sectionId, tabType });
        }
        break;

      case 'pregnancy-tab':
        console.log('✅ ENTERED PREGNANCY-TAB CASE!');
        const targetTab = target.dataset.tab;
        console.log('🎯 Pregnancy tab clicked via event delegation:', targetTab);
        console.log('🔧 Target button classes:', target.classList.toString());
        
        if (targetTab) {
          // Remove active class from all pregnancy tab buttons and panes
          const pregnancyTabBtns = document.querySelectorAll('.pregnancy-tab-btn');
          const pregnancyTabPanes = document.querySelectorAll('.pregnancy-tab-pane');
          
          console.log('🔧 Found', pregnancyTabBtns.length, 'pregnancy tab buttons');
          console.log('🔧 Found', pregnancyTabPanes.length, 'pregnancy tab panes');
          
          pregnancyTabBtns.forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
            console.log('🔧 Removed active from button:', b.id);
          });
          pregnancyTabPanes.forEach(p => {
            p.classList.remove('active');
            console.log('🔧 Removed active from pane:', p.id);
          });

          // Add active class to clicked button and corresponding pane
          target.classList.add('active');
          target.setAttribute('aria-selected', 'true');
          console.log('🔧 Added active to button:', target.id);
          
          const targetPane = document.getElementById(targetTab);
          if (targetPane) {
            targetPane.classList.add('active');
            console.log('✅ Activated pregnancy tab pane:', targetTab);
          } else {
            console.warn('❌ Could not find pregnancy tab pane:', targetTab);
            console.log('🔧 Available pregnancy panes:', Array.from(pregnancyTabPanes).map(p => p.id));
          }
        } else {
          console.error('❌ Missing target tab for pregnancy tab action');
          console.log('🔧 Button dataset:', target.dataset);
        }
        console.log('✅ LEAVING PREGNANCY-TAB CASE!');
        break;

      case 'show-pdf-viewer':
        const pdfIndex1 = target.dataset.pdfIndex;
        console.log('PDF viewer show requested for index:', pdfIndex1);

        // Show the PDF viewer container
        const viewerContainer1 = document.getElementById(`pdf-viewer-${pdfIndex1}`);
        if (viewerContainer1) {
          viewerContainer1.classList.remove('hidden');

          // Update button to show "Hide" instead of "View"
          const buttonIcon = target.querySelector('i');
          const buttonText = target.childNodes[target.childNodes.length - 1];
          if (buttonIcon && buttonText) {
            buttonIcon.className = 'fa-solid fa-eye-slash me-1';
            buttonText.textContent = 'Hide';
          }

          // Change button action to hide
          target.dataset.action = 'hide-pdf-viewer';
          console.log('✅ OrCD viewer shown for index:', pdfIndex1);
        } else {
          console.warn('❌ Could not find OrCD viewer container for index:', pdfIndex1);
        }
        break;

      case 'hide-pdf-viewer':
        const pdfIndex3 = target.dataset.pdfIndex;
        console.log('OrCD viewer hide requested for index:', pdfIndex3);

        // Hide the OrCD viewer container
        const viewerContainer3 = document.getElementById(`pdf-viewer-${pdfIndex3}`);
        if (viewerContainer3) {
          viewerContainer3.classList.add('hidden');

          // Update button to show "View" instead of "Hide"
          const buttonIcon = target.querySelector('i');
          const buttonText = target.childNodes[target.childNodes.length - 1];
          if (buttonIcon && buttonText) {
            buttonIcon.className = 'fa-solid fa-eye me-1';
            buttonText.textContent = 'View';
          }

          // Change button action back to show
          target.dataset.action = 'show-pdf-viewer';
          console.log('✅ OrCD viewer hidden for index:', pdfIndex3);
        } else {
          console.warn('❌ Could not find OrCD viewer container for index:', pdfIndex3);
        }
        break;

      case 'open-pdf-fullscreen':
        const pdfIndex2 = target.dataset.pdfIndex;
        console.log('OrCD fullscreen requested for index:', pdfIndex2);

        // Find the iframe for this PDF and attempt fullscreen
        const iframe = document.getElementById(`pdf-frame-${pdfIndex2}`);
        if (iframe) {
          if (iframe.requestFullscreen) {
            iframe.requestFullscreen().catch(err => console.warn('Fullscreen error:', err));
          } else if (iframe.webkitRequestFullscreen) {
            iframe.webkitRequestFullscreen();
          } else if (iframe.msRequestFullscreen) {
            iframe.msRequestFullscreen();
          } else {
            console.warn('Fullscreen not supported by browser');
            // Fallback: open in new window
            const src = iframe.src;
            if (src) {
              window.open(src, '_blank', 'width=1200,height=800');
            }
          }
        } else {
          console.warn('❌ Could not find iframe for fullscreen:', pdfIndex2);
        }
        break;

      case 'open-pdf-new-tab':
        const pdfIndex4 = target.dataset.pdfIndex;
        console.log('PDF new tab requested for index:', pdfIndex4);
        if (pdfIndex4 !== undefined) {
          // Try to open PDF directly by finding the download link
          const pdfContainer = target.closest('.pdf-item') || target.closest('.pdf-document');
          const downloadLink = pdfContainer ? pdfContainer.querySelector('a[href*=".pdf"]') : null;
          if (downloadLink) {
            window.open(downloadLink.href, '_blank');
          } else {
            console.warn('Could not find PDF download link');
          }
        }
        break;

      case 'open-pdf-directly':
        console.log('Direct PDF open requested');
        console.warn('Direct PDF functionality not available in enhanced CDA view');
        break;

      default:
        console.log('Unknown action:', action);
        break;
    }
  }, true); // Use capture phase to run before other event listeners

  // Mark as initialized to prevent duplicate listeners
  extendedContainer.dataset.initialized = 'true';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeEnhancedCDA);

// Global debugging function - you can call this from browser console
window.debugTabs = function () {
  console.log('🔍 DEBUG: Tab Status Report');
  const allTabs = document.querySelectorAll('.clinical-tab-content');
  allTabs.forEach(tab => {
    console.log(`Tab ${tab.id}:`, {
      hasActiveClass: tab.classList.contains('active'),
      opacity: window.getComputedStyle(tab).opacity,
      visibility: window.getComputedStyle(tab).visibility,
      zIndex: window.getComputedStyle(tab).zIndex,
      display: window.getComputedStyle(tab).display
    });
  });
};

/**
 * Pregnancy History Tab Navigation
 * Handles mobile-first tab switching for pregnancy history section
 */
function initializePregnancyHistoryTabs() {
  console.log('🔧 Initializing pregnancy history tabs...');
  
  const pregnancyTabBtns = document.querySelectorAll('.pregnancy-tab-btn');
  const pregnancyTabPanes = document.querySelectorAll('.pregnancy-tab-pane');

  console.log('🔍 Found pregnancy tab buttons:', pregnancyTabBtns.length);
  console.log('🔍 Found pregnancy tab panes:', pregnancyTabPanes.length);

  if (pregnancyTabBtns.length === 0) {
    console.log('⚠️ No pregnancy tab buttons found, skipping initialization');
    return;
  }

  pregnancyTabBtns.forEach((btn, index) => {
    console.log(`🔍 Tab button ${index}:`, btn.getAttribute('data-tab'), btn.textContent.trim());
    
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const targetTab = this.getAttribute('data-tab');
      
      console.log('🎯 Pregnancy tab clicked:', targetTab);

      // Remove active class from all buttons and panes
      pregnancyTabBtns.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      pregnancyTabPanes.forEach(p => {
        p.classList.remove('active');
        console.log('🔧 Removing active from pane:', p.id);
      });

      // Add active class to clicked button and corresponding pane
      this.classList.add('active');
      this.setAttribute('aria-selected', 'true');
      const targetPane = document.getElementById(targetTab);
      if (targetPane) {
        targetPane.classList.add('active');
        console.log('✅ Activated pregnancy tab pane:', targetTab);
      } else {
        console.warn('❌ Could not find pregnancy tab pane:', targetTab);
      }

      // Announce change to screen readers
      const announcement = `Switched to ${this.textContent.trim()} tab`;
      if (typeof announceToScreenReader === 'function') {
        announceToScreenReader(announcement);
      }
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

  console.log('✅ Pregnancy history tabs initialized');
}

// Global function to manually activate any tab - you can call this from browser console
window.forceActivateTab = function (tabId) {
  console.log(`🔧 FORCING activation of: ${tabId}`);
  const allTabs = document.querySelectorAll('.clinical-tab-content');
  allTabs.forEach(tab => tab.classList.remove('active'));

  const targetTab = document.getElementById(tabId);
  if (targetTab) {
    targetTab.classList.add('active');
    console.log(`✅ Forced ${tabId} to active state`);
    window.debugTabs();
  } else {
    console.log(`❌ Tab ${tabId} not found`);
  }
};
