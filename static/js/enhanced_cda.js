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
  console.log('🎯 Initializing default tab...');
  setTimeout(() => {
    console.log('🎯 Delayed initialization - checking if elements exist...');
    const personalTab = document.getElementById('extended_patient_personal');
    const healthcareTab = document.getElementById('extended_patient_healthcare');

    console.log('🎯 Elements found:', {
      personal: personalTab ? 'EXISTS' : 'MISSING',
      healthcare: healthcareTab ? 'EXISTS' : 'MISSING'
    });

    if (personalTab) {
      showExtendedTab('extended_patient', 'personal');
    } else {
      console.error('❌ Cannot initialize - personal tab element not found');
    }
  }, 100); // Small delay to ensure DOM is ready

  console.log('Bootstrap functionality initialized');
}

/**
 * Extended Patient Tab Management Function
 * @param {string} sectionId - ID of the section containing tabs
 * @param {string} tabType - Type of tab to show (personal, healthcare, system, clinical, pdfs)
 */
function showExtendedTab(sectionId, tabType) {
  console.log('🎯 Switching tab:', tabType, 'for section:', sectionId);

  // Hide all tab contents for the extended patient section
  const personalTab = document.getElementById(sectionId + '_personal');
  const healthcareTab = document.getElementById(sectionId + '_healthcare');
  const systemTab = document.getElementById(sectionId + '_system');
  const clinicalTab = document.getElementById(sectionId + '_clinical');
  const pdfsTab = document.getElementById(sectionId + '_pdfs');

  console.log('📋 Tab elements found:', {
    personal: personalTab ? 'EXISTS' : 'MISSING',
    healthcare: healthcareTab ? 'EXISTS' : 'MISSING',
    system: systemTab ? 'EXISTS' : 'MISSING',
    clinical: clinicalTab ? 'EXISTS' : 'MISSING',
    pdfs: pdfsTab ? 'EXISTS' : 'MISSING'
  });

  // Find the parent extended patient container
  const extendedContainer = personalTab ? personalTab.closest('.clinical-section') :
    (healthcareTab ? healthcareTab.closest('.clinical-section') :
      (systemTab ? systemTab.closest('.clinical-section') :
        (clinicalTab ? clinicalTab.closest('.clinical-section') :
          (pdfsTab ? pdfsTab.closest('.clinical-section') : null))));

  if (!extendedContainer) {
    console.error('❌ Extended patient container not found for:', sectionId);
    return;
  }

  const buttons = extendedContainer.querySelectorAll('.tab-navigation .tab-button');
  const allTabs = [personalTab, healthcareTab, systemTab, clinicalTab, pdfsTab].filter(tab => tab !== null);

  // Hide all tabs using direct style manipulation (more reliable than CSS classes)
  allTabs.forEach(tab => {
    if (tab) {
      tab.classList.remove('active');
      // Remove direct styles to let CSS handle everything
      tab.style.display = '';
      tab.style.visibility = '';
      tab.style.opacity = '';
    }
  });

  // Remove active class from all buttons
  buttons.forEach(btn => btn.classList.remove('active'));

  // Show selected tab and activate corresponding button
  let activeTab = null;
  let activeButtonIndex = -1;

  if (tabType === 'personal' && personalTab) {
    activeTab = personalTab;
    activeButtonIndex = 0;
  } else if (tabType === 'healthcare' && healthcareTab) {
    activeTab = healthcareTab;
    activeButtonIndex = 1;
  } else if (tabType === 'system' && systemTab) {
    activeTab = systemTab;
    activeButtonIndex = 2;
  } else if (tabType === 'clinical' && clinicalTab) {
    activeTab = clinicalTab;
    activeButtonIndex = 3;
  } else if (tabType === 'pdfs' && pdfsTab) {
    activeTab = pdfsTab;
    activeButtonIndex = pdfsTab ? 4 : -1;
  }

  if (activeTab) {
    console.log('✅ Activating tab:', activeTab.id);

    // FORCE the active class with aggressive logging
    activeTab.classList.add('active');
    console.log('🔧 FORCED active class added');
    console.log('🔧 classList contains active:', activeTab.classList.contains('active'));
    console.log('🔧 className:', activeTab.className);

    // Force CSS to refresh by triggering reflow
    activeTab.offsetHeight; // Trigger reflow

    // Let CSS handle visibility - remove direct style manipulation
    activeTab.style.display = '';
    activeTab.style.visibility = '';
    activeTab.style.opacity = '';

    console.log('🔧 Tab classes after activation:', activeTab.className);
    console.log('🔧 Computed opacity:', window.getComputedStyle(activeTab).opacity);
    console.log('🔧 Computed visibility:', window.getComputedStyle(activeTab).visibility);
    console.log('🔧 Computed z-index:', window.getComputedStyle(activeTab).zIndex);
    console.log('🔧 Element dimensions:', {
      width: activeTab.offsetWidth,
      height: activeTab.offsetHeight,
      scrollHeight: activeTab.scrollHeight,
      clientHeight: activeTab.clientHeight
    });

    // Check if content is actually there
    console.log('🔧 Tab innerHTML length:', activeTab.innerHTML.length);
    console.log('🔧 Tab children count:', activeTab.children.length);
  } else {
    console.log('❌ No tab found for type:', tabType);
  }

  if (activeButtonIndex >= 0 && buttons[activeButtonIndex]) {
    buttons[activeButtonIndex].classList.add('active');
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

      case 'show-pdf-viewer':
        const pdfIndex1 = target.dataset.pdfIndex;
        console.log('PDF viewer requested for index:', pdfIndex1);
        // PDF functionality not implemented in enhanced_cda.js
        console.warn('PDF viewer functionality not available in enhanced CDA view');
        break;

      case 'open-pdf-fullscreen':
        const pdfIndex2 = target.dataset.pdfIndex;
        console.log('PDF fullscreen requested for index:', pdfIndex2);
        console.warn('PDF fullscreen functionality not available in enhanced CDA view');
        break;

      case 'hide-pdf-viewer':
        const pdfIndex3 = target.dataset.pdfIndex;
        console.log('Hide PDF viewer requested for index:', pdfIndex3);
        console.warn('Hide PDF viewer functionality not available in enhanced CDA view');
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
