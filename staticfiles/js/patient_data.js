// ============================================================================
// PATIENT DATA FUNCTIONALITY
// ============================================================================
// JavaScript for patient search, break glass, and file upload functionality

// Global variables for service requests
let currentServiceId = null;
let currentServiceName = null;

/**
 * Break Glass Reason Toggle
 * Shows/hides emergency reason textarea based on checkbox state
 */
function toggleBreakGlassReason() {
  const checkbox = document.getElementById('break_glass');
  const reasonSection = document.getElementById('breakGlassReason');
  const reasonTextarea = document.getElementById('break_glass_reason_text');

  if (checkbox.checked) {
    reasonSection.classList.remove('hidden');
    reasonTextarea.required = true;
  } else {
    reasonSection.classList.add('hidden');
    reasonTextarea.required = false;
    reasonTextarea.value = '';
  }
}

/**
 * Date Input Formatting
 * Auto-formats birthdate input as YYYY/MM/DD
 */
function initializeDateFormatting() {
  const birthdateInput = document.getElementById('birthdate');
  if (!birthdateInput) return;

  birthdateInput.addEventListener('input', function (e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length >= 4) {
      value = value.substring(0, 4) + '/' + value.substring(4);
    }
    if (value.length >= 7) {
      value = value.substring(0, 7) + '/' + value.substring(7, 9);
    }
    e.target.value = value;
  });
}

/**
 * File Upload Functionality
 * Handles CDA file upload with drag/drop and validation
 */
function initializeFileUpload() {
  const fileInput = document.getElementById('cda_file');
  const fileLabel = document.querySelector('.file-upload-label');
  const feedback = document.getElementById('fileUploadFeedback');

  if (!fileInput || !fileLabel || !feedback) return;

  fileInput.addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
      // Update label text
      const uploadText = fileLabel.querySelector('.upload-text');
      uploadText.textContent = file.name;

      // Validate file type
      const validExtensions = ['.xml', '.cda'];
      const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

      if (!validExtensions.includes(fileExtension)) {
        feedback.innerHTML = '<span class="text-error">⚠️ Please select an XML or CDA file</span>';
        feedback.classList.remove('hidden');
        fileLabel.classList.add('upload-error');
        fileLabel.classList.remove('upload-ready');
      } else {
        feedback.innerHTML = '<span class="text-success">✅ File ready for upload</span>';
        feedback.classList.remove('hidden');
        fileLabel.classList.remove('upload-error');
        fileLabel.classList.add('upload-ready');
      }
    } else {
      // Reset to original state
      const uploadText = fileLabel.querySelector('.upload-text');
      uploadText.textContent = 'Choose CDA File';
      feedback.classList.add('hidden');
      fileLabel.classList.remove('upload-error', 'upload-ready');
    }
  });

  // Drag and drop functionality
  fileLabel.addEventListener('dragover', function (e) {
    e.preventDefault();
    fileLabel.classList.add('upload-dragover');
  });

  fileLabel.addEventListener('dragleave', function (e) {
    e.preventDefault();
    fileLabel.classList.remove('upload-dragover');
  });

  fileLabel.addEventListener('drop', function (e) {
    e.preventDefault();
    fileLabel.classList.remove('upload-dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      fileInput.dispatchEvent(new Event('change'));
    }
  });
}

/**
 * Patient Search Results Functionality
 * ============================================================================
 */

/**
 * Request Service Handler
 * Handles service requests with consent method checking
 */
function requestService(serviceId, serviceName) {
  currentServiceId = serviceId;
  currentServiceName = serviceName;

  const consentMethod = document.querySelector(`input[name="consent_${serviceId}"]:checked`).value;

  if (consentMethod === 'BREAK_GLASS') {
    const modal = document.getElementById('breakGlassModal');
    modal.classList.add('show');
  } else {
    submitServiceRequest(serviceId, consentMethod, '');
  }
}

/**
 * Close Break Glass Modal
 * Closes the emergency access modal and clears form
 */
function closeBreakGlassModal() {
  const modal = document.getElementById('breakGlassModal');
  modal.classList.remove('show');
  document.getElementById('emergencyReason').value = '';
}

/**
 * Confirm Break Glass Access
 * Validates and submits emergency access request
 */
function confirmBreakGlass() {
  const reason = document.getElementById('emergencyReason').value.trim();
  if (!reason) {
    alert('Please provide a reason for emergency access.');
    return;
  }

  submitServiceRequest(currentServiceId, 'BREAK_GLASS', reason);
  closeBreakGlassModal();
}

/**
 * View Local CDA Document
 * Navigates to CDA document view
 */
function viewLocalCDADocument(documentIndex) {
  // Note: URL template replacement done in template
  const urlTemplate = window.localCDADocumentURL || '';
  if (urlTemplate) {
    window.location.href = urlTemplate.replace('__INDEX__', documentIndex);
  }
}

/**
 * Submit Service Request
 * Makes AJAX request to submit service request
 */
function submitServiceRequest(serviceId, consentMethod, breakGlassReason) {
  const url = window.requestPatientServiceURL || '';
  const patientId = window.patientIdentifierId || 0;
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  if (!url || !patientId) {
    alert('Configuration error: Missing required URLs or patient ID');
    return;
  }

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
      patient_identifier_id: patientId,
      service_id: serviceId,
      consent_method: consentMethod,
      break_glass_reason: breakGlassReason
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert(`${data.message}\nRequest ID: ${data.request_id}`);
        location.reload(); // Refresh to show updated data
      } else {
        alert(`Error: ${data.error}`);
      }
    })
    .catch(error => {
      alert('An error occurred while processing your request.');
      console.error('Error:', error);
    });
}

/**
 * Initialize Break Glass Modal
 * Sets up modal event handlers
 */
function initializeBreakGlassModal() {
  const modal = document.getElementById('breakGlassModal');
  if (!modal) return;

  // Debug: Check if modal is visible on page load
  if (modal.style.display !== 'none') {
    console.warn('Modal is visible on page load, hiding it');
    modal.style.display = 'none';
  }

  // Close modal when clicking outside
  modal.addEventListener('click', function (e) {
    if (e.target === this) {
      closeBreakGlassModal();
    }
  });
}

/**
 * Patient ORCD Functionality
 * ============================================================================
 */

/**
 * Download ORCD PDF
 * Initiates download of ORCD PDF file
 */
function downloadORCD() {
  const downloadUrl = window.orcdDownloadURL;
  const orcdAvailable = window.orcdAvailable;

  if (orcdAvailable && downloadUrl) {
    window.location.href = downloadUrl;
  } else {
    alert('PDF is not available for this document. This could be because the source document is L3 CDA only (no embedded PDF).');
  }
}

/**
 * Open Fullscreen Modal
 * Opens PDF in fullscreen modal overlay
 */
function openFullscreen() {
  const orcdAvailable = window.orcdAvailable;
  const viewUrl = window.orcdViewURL;

  if (!orcdAvailable || !viewUrl) {
    alert('PDF is not available for fullscreen viewing.');
    return;
  }

  const modal = document.getElementById('fullscreenModal');
  const iframe = document.getElementById('fullscreenPdfFrame');

  // Set the PDF source URL
  iframe.src = viewUrl;

  // Show modal with animation
  modal.style.display = 'block';
  setTimeout(() => {
    modal.classList.add('show');
  }, 10);

  // Add escape key listener
  document.addEventListener('keydown', handleEscapeKey);

  // Prevent body scroll
  document.body.style.overflow = 'hidden';
}

/**
 * Close Fullscreen Modal
 * Closes fullscreen PDF modal
 */
function closeFullscreen() {
  const modal = document.getElementById('fullscreenModal');
  const iframe = document.getElementById('fullscreenPdfFrame');

  // Start close animation
  modal.classList.remove('show');

  // Hide modal after animation
  setTimeout(() => {
    modal.style.display = 'none';
    // Clear iframe source to stop loading
    iframe.src = '';
  }, 300);

  // Remove escape key listener
  document.removeEventListener('keydown', handleEscapeKey);

  // Restore body scroll
  document.body.style.overflow = '';
}

/**
 * Handle Escape Key
 * Closes fullscreen modal when Escape key is pressed
 */
function handleEscapeKey(event) {
  if (event.key === 'Escape') {
    closeFullscreen();
  }
}

/**
 * Open PDF in New Tab
 * Opens PDF directly in new browser tab
 */
function openPdfDirectly() {
  const orcdAvailable = window.orcdAvailable;
  const viewUrl = window.orcdViewURL;

  if (orcdAvailable && viewUrl) {
    window.open(viewUrl, '_blank');
  } else {
    alert('PDF is not available for direct viewing.');
  }
}

/**
 * Initialize ORCD Functionality
 * Sets up ORCD PDF viewing functionality
 */
function initializeORCD() {
  const modal = document.getElementById('fullscreenModal');
  if (!modal) return;

  // Close fullscreen when clicking outside the content
  modal.addEventListener('click', function (event) {
    // Only close if clicking the modal background, not the content
    if (event.target === modal) {
      closeFullscreen();
    }
  });

  // Test PDF loading on page load if available
  const orcdAvailable = window.orcdAvailable;
  if (orcdAvailable) {
    const iframe = document.getElementById('pdfFrame');
    if (iframe) {
      iframe.onload = function () {
        console.log('PDF iframe loaded successfully');
      };

      iframe.onerror = function () {
        console.error('Failed to load PDF in iframe');
      };
    }
  }
}

/**
 * Extended Patient Info Component Functionality
 * ============================================================================
 */

// Global patient ID for PDF operations
let PATIENT_ID = '';

/**
 * Set Patient ID for PDF operations
 * Called by templates to configure patient context
 */
function setPatientId(patientId) {
  PATIENT_ID = patientId;
}

/**
 * Extended Patient Tab Management
 * Shows/hides tabs within extended patient sections
 */
function showExtendedTab(sectionId, tabType) {
  console.log('🎯 Switching Extended Patient tab:', sectionId, tabType);

  // Hide all tab contents for the extended patient section
  const personalTab = document.getElementById(sectionId + '_personal');
  const healthcareTab = document.getElementById(sectionId + '_healthcare');
  const systemTab = document.getElementById(sectionId + '_system');
  const clinicalTab = document.getElementById(sectionId + '_clinical');
  const pdfsTab = document.getElementById(sectionId + '_pdfs');

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

  // Hide all tabs first
  [personalTab, healthcareTab, systemTab, clinicalTab, pdfsTab].forEach(tab => {
    if (tab) {
      tab.classList.remove('active');
      // Don't use inline styles - let CSS handle visibility
    }
  });

  // Remove active class from all tab buttons in this section
  const tabButtons = extendedContainer.querySelectorAll('.tab-button');
  tabButtons.forEach(btn => btn.classList.remove('active'));

  // Show the selected tab
  const targetTab = document.getElementById(sectionId + '_' + tabType);
  if (targetTab) {
    targetTab.classList.add('active');
    // Don't use inline styles - let CSS handle visibility
    console.log('✅ Extended tab shown:', sectionId + '_' + tabType);
  }

  // Activate the corresponding tab button
  const activeButton = extendedContainer.querySelector(`[data-tab-type="${tabType}"]`);
  if (activeButton) {
    activeButton.classList.add('active');
    console.log('✅ Tab button activated:', tabType);
  }
}

/**
 * PDF Viewer Functions
 * Shows/hides PDF viewers within extended patient info
 */
function showPDFViewer(pdfIndex) {
  console.log('🔍 Opening PDF viewer for index:', pdfIndex);

  const viewer = document.getElementById('pdf-viewer-' + pdfIndex);

  if (viewer) {
    if (viewer.classList.contains('hidden') || viewer.style.display === 'none' || viewer.style.display === '') {
      viewer.classList.remove('hidden');
      viewer.style.display = 'block';
      console.log('✅ PDF viewer opened for index:', pdfIndex);

      // Scroll to the viewer to ensure it's visible
      viewer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      viewer.classList.add('hidden');
      viewer.style.display = 'none';
      console.log('🔒 PDF viewer closed for index:', pdfIndex);
    }
  } else {
    console.error('❌ PDF viewer not found for index:', pdfIndex);
  }
}

/**
 * Open PDF in Fullscreen Modal
 * Opens PDF in fullscreen overlay for better viewing
 */
function openPDFFullscreen(pdfIndex) {
  console.log('🔍 Opening PDF fullscreen for index:', pdfIndex);

  if (!PATIENT_ID) {
    console.error('❌ Patient ID not set for PDF viewing');
    return;
  }

  // Construct PDF URL (template should provide this pattern)
  const pdfUrl = window.pdfViewUrl ? window.pdfViewUrl.replace('__INDEX__', pdfIndex) :
    `/patient_data/patient/${PATIENT_ID}/pdf/${pdfIndex}/view/`;

  // Create or show fullscreen modal
  let modal = document.getElementById('pdf-fullscreen-modal');
  if (!modal) {
    modal = createPDFFullscreenModal();
  }

  const iframe = modal.querySelector('iframe');
  iframe.src = pdfUrl;

  modal.style.display = 'block';
  setTimeout(() => modal.classList.add('show'), 10);

  // Prevent body scroll
  document.body.style.overflow = 'hidden';
}

/**
 * Handle PDF Load Errors
 * Shows fallback content when PDF fails to load
 */
function handlePDFLoadError(pdfIndex) {
  console.warn('⚠️ PDF failed to load for index:', pdfIndex);

  const viewer = document.getElementById('pdf-viewer-' + pdfIndex);
  const fallback = document.getElementById('pdf-fallback-' + pdfIndex);

  if (viewer && fallback) {
    viewer.style.display = 'none';
    fallback.classList.remove('hidden');
    fallback.style.display = 'block';
  }
}

/**
 * Create PDF Fullscreen Modal
 * Creates modal DOM elements for fullscreen PDF viewing
 */
function createPDFFullscreenModal() {
  const modal = document.createElement('div');
  modal.id = 'pdf-fullscreen-modal';
  modal.className = 'fullscreen-modal hidden';

  modal.innerHTML = `
        <div class="fullscreen-content">
            <div class="fullscreen-header">
                <div class="fullscreen-title">
                    <h2>PDF Document</h2>
                </div>
                <div class="fullscreen-controls">
                    <button class="btn btn-secondary" onclick="closePDFFullscreen()">
                        <i class="fas fa-times"></i> Close
                    </button>
                </div>
            </div>
            <div class="fullscreen-pdf-container">
                <iframe class="fullscreen-pdf-frame" frameborder="0"></iframe>
            </div>
        </div>
    `;

  document.body.appendChild(modal);

  // Add click outside to close
  modal.addEventListener('click', function (e) {
    if (e.target === modal) {
      closePDFFullscreen();
    }
  });

  return modal;
}

/**
 * Close PDF Fullscreen Modal
 * Closes the fullscreen PDF modal
 */
function closePDFFullscreen() {
  const modal = document.getElementById('pdf-fullscreen-modal');
  if (modal) {
    modal.classList.remove('show');
    setTimeout(() => {
      modal.style.display = 'none';
      modal.querySelector('iframe').src = '';
    }, 300);
  }

  // Restore body scroll
  document.body.style.overflow = '';
}

/**
 * Hide PDF Viewer
 * Hides the PDF viewer container for a specific index
 */
function hidePDFViewer(pdfIndex) {
  const viewer = document.getElementById(`pdf-viewer-${pdfIndex}`);
  if (viewer) {
    viewer.classList.add('hidden');
  }
}

/**
 * Open PDF in New Tab
 * Opens PDF in a new browser tab
 */
function openPDFInNewTab(pdfIndex) {
  // Construct the PDF URL - this matches the pattern used in templates
  const baseUrl = window.location.origin;
  const pdfUrl = `${baseUrl}/patient_data/view_pdf/${window.patientId || ''}/${pdfIndex}/`;
  window.open(pdfUrl, '_blank');
}

/**
 * Initialize all patient data functionality
 * Called when DOM is ready
 */
function initializePatientData() {
  toggleBreakGlassReason();

  // Add event listener for break glass checkbox
  const breakGlassCheckbox = document.getElementById('break_glass');
  if (breakGlassCheckbox) {
    breakGlassCheckbox.addEventListener('change', toggleBreakGlassReason);
  }

  initializeDateFormatting();
  initializeFileUpload();
  initializeBreakGlassModal();
  initializeORCD();
  initializeClinicalAccordion();
  initializeResultsPageEventDelegation();
  initializeORCDEventDelegation();

  // Try to initialize extended patient immediately
  initializeExtendedPatientEventDelegation();

  // Also initialize when the Extended Patient tab becomes active
  const extendedTab = document.getElementById('extended-tab');
  if (extendedTab) {
    console.log('🎧 Adding Bootstrap tab event listener for extended patient');
    extendedTab.addEventListener('shown.bs.tab', function (event) {
      console.log('🎯 Extended Patient tab shown, initializing event delegation');
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        initializeExtendedPatientEventDelegation();
      }, 100);
    });
  }
}

/**
 * Initialize event delegation for search results page
 * Uses data attributes instead of inline event handlers
 */
function initializeResultsPageEventDelegation() {
  const resultsContainer = document.querySelector('.results-container');
  if (!resultsContainer) return;

  // Set global configuration variables from data attributes
  window.requestPatientServiceURL = resultsContainer.dataset.requestServiceUrl || '';
  window.localCDADocumentURL = resultsContainer.dataset.localCdaUrl || '';
  window.patientIdentifierId = resultsContainer.dataset.patientId || 0;

  // Event delegation for all clickable elements with data-action
  resultsContainer.addEventListener('click', function (event) {
    const target = event.target;
    const action = target.dataset.action;

    switch (action) {
      case 'view-local-cda':
        const documentIndex = target.dataset.documentIndex;
        if (documentIndex !== undefined) {
          viewLocalCDADocument(documentIndex);
        }
        break;

      case 'request-service':
        const serviceId = target.dataset.serviceId;
        const serviceName = target.dataset.serviceName;
        if (serviceId && serviceName) {
          requestService(serviceId, serviceName);
        }
        break;

      case 'close-break-glass-modal':
        closeBreakGlassModal();
        break;

      case 'confirm-break-glass':
        confirmBreakGlass();
        break;
    }
  });
}

/**
 * Initialize event delegation for ORCD page
 * Uses data attributes instead of inline event handlers
 */
function initializeORCDEventDelegation() {
  const orcdContainer = document.querySelector('.orcd-container');
  if (!orcdContainer) return;

  // Set global configuration variables from data attributes
  window.orcdAvailable = orcdContainer.dataset.orcdAvailable === 'true';
  window.orcdDownloadURL = orcdContainer.dataset.downloadUrl || '';
  window.orcdViewURL = orcdContainer.dataset.viewUrl || '';

  // Event delegation for all clickable elements with data-action
  orcdContainer.addEventListener('click', function (event) {
    const target = event.target;
    const action = target.dataset.action;

    switch (action) {
      case 'open-fullscreen':
        openFullscreen();
        break;

      case 'open-pdf-directly':
        openPdfDirectly();
        break;

      case 'download-orcd':
        downloadORCD();
        break;

      case 'close-fullscreen':
        closeFullscreen();
        break;
    }
  });
}

/**
 * Initialize event delegation for extended patient info component
 * Uses data attributes instead of inline event handlers
 */
function initializeExtendedPatientEventDelegation() {
  const allClinicalSections = document.querySelectorAll('.clinical-section');
  console.log('🔍 Found', allClinicalSections.length, 'clinical-section elements:', allClinicalSections);

  const extendedContainer = document.querySelector('#extendedPatientSection');
  console.log('🎯 Looking for #extendedPatientSection specifically:', extendedContainer);

  if (!extendedContainer) {
    console.warn('⚠️ No #extendedPatientSection container found for extended patient event delegation');
    return;
  }

  // Check if already initialized to prevent duplicate listeners
  if (extendedContainer.dataset.initialized === 'true') {
    console.log('🔄 Extended patient event delegation already initialized, skipping');
    return;
  }

  console.log('✅ Found extended patient container:', extendedContainer.id, extendedContainer);

  // Set patient ID from data attribute for PDF functions
  window.patientId = extendedContainer.dataset.patientId || '';
  console.log('💾 Set patient ID:', window.patientId);

  // Event delegation for all clickable elements with data-action
  console.log('🎧 Attaching click event listener to extended patient container');

  // Also check if the buttons are actually clickable
  const tabButtons = extendedContainer.querySelectorAll('.tab-button');
  console.log('🔘 Found', tabButtons.length, 'tab buttons in container:', tabButtons);
  tabButtons.forEach((btn, index) => {
    console.log(`Button ${index}:`, btn, 'data-action:', btn.dataset.action, 'data-tab-type:', btn.dataset.tabType);

    // Also attach direct event listeners as a fallback
    btn.addEventListener('click', function (e) {
      console.log('🎯 Direct button click detected:', this.dataset.action, this.dataset.tabType);
      e.preventDefault();
      e.stopPropagation();

      if (this.dataset.action === 'show-extended-tab') {
        const sectionId = this.dataset.sectionId;
        const tabType = this.dataset.tabType;
        if (sectionId && tabType) {
          showExtendedTab(sectionId, tabType);
        }
      }
    });
  });

  extendedContainer.addEventListener('click', function (event) {
    // Find the closest button with data-action (in case user clicks on icon or text inside button)
    const target = event.target.closest('[data-action]') || event.target;
    const action = target.dataset.action;

    console.log('🖱️ Extended patient click - Target:', event.target, 'Closest with data-action:', target, 'Action:', action);

    // If we found a button with an action, prevent Bootstrap from interfering
    if (action) {
      event.preventDefault();
      event.stopPropagation();
      console.log('🛑 Prevented default and stopped propagation for action:', action);

      // Check if THIS SPECIFIC button is disabled
      if (target.disabled || target.dataset.disabled === 'true') {
        console.log('🚫 Button with action "' + action + '" is disabled, ignoring click');
        return;
      }
    } else {
      console.log('🤷 No action found on clicked element, allowing event to bubble');
      return;
    }

    switch (action) {
      case 'show-extended-tab':
        const sectionId = target.dataset.sectionId;
        const tabType = target.dataset.tabType;
        console.log('🎯 Tab switch requested:', sectionId, tabType);
        if (sectionId && tabType) {
          showExtendedTab(sectionId, tabType);
        }
        break;

      case 'show-pdf-viewer':
        const pdfIndex1 = target.dataset.pdfIndex;
        if (pdfIndex1 !== undefined) {
          showPDFViewer(pdfIndex1);
        }
        break;

      case 'open-pdf-fullscreen':
        const pdfIndex2 = target.dataset.pdfIndex;
        if (pdfIndex2 !== undefined) {
          openPDFFullscreen(pdfIndex2);
        }
        break;

      case 'hide-pdf-viewer':
        const pdfIndex3 = target.dataset.pdfIndex;
        if (pdfIndex3 !== undefined) {
          hidePDFViewer(pdfIndex3);
        }
        break;

      case 'open-pdf-new-tab':
        const pdfIndex4 = target.dataset.pdfIndex;
        if (pdfIndex4 !== undefined) {
          openPDFInNewTab(pdfIndex4);
        }
        break;
    }
  }, true); // Use capture phase to run before other event listeners

  // Add a test function to debug button functionality
  window.testExtendedPatientButtons = function () {
    console.log('🧪 Testing extended patient buttons...');
    const container = document.querySelector('.extended-patient-content');
    if (!container) {
      console.log('❌ No extended patient container found');
      return;
    }

    const buttons = container.querySelectorAll('.tab-button');
    console.log('🔘 Found', buttons.length, 'tab buttons');

    buttons.forEach((btn, index) => {
      console.log(`Button ${index}:`, btn.outerHTML.substring(0, 100) + '...');
      console.log(`  data-action: ${btn.dataset.action}`);
      console.log(`  data-tab-type: ${btn.dataset.tabType}`);
      console.log(`  disabled: ${btn.disabled}`);
      console.log(`  data-disabled: ${btn.dataset.disabled}`);
      console.log(`  computed style pointer-events: ${getComputedStyle(btn).pointerEvents}`);
      console.log(`  offsetParent: ${btn.offsetParent}`);
    });

    // Try clicking the personal button programmatically
    const personalBtn = container.querySelector('[data-tab-type="personal"]');
    if (personalBtn) {
      console.log('🎯 Testing personal button click...');
      personalBtn.click();
    } else {
      console.log('❌ Personal button not found');
    }
  };

  // Mark as initialized to prevent duplicate listeners
  extendedContainer.dataset.initialized = 'true';
  console.log('✅ Extended patient event delegation initialized successfully');
}

// ============================================================================
// CLINICAL INFORMATION ACCORDION FUNCTIONALITY
// ============================================================================

/**
 * Toggle individual clinical section
 * @param {string} sectionId - ID of the section to toggle
 */
function toggleSection(sectionId) {
  const section = document.getElementById(sectionId);
  const button = document.querySelector(`[aria-controls="${sectionId}"]`);

  if (!section || !button) {
    console.warn('Section or button not found:', sectionId);
    return;
  }

  if (section.classList.contains('show')) {
    section.classList.remove('show');
    button.setAttribute('aria-expanded', 'false');
    button.classList.add('collapsed');
  } else {
    section.classList.add('show');
    button.setAttribute('aria-expanded', 'true');
    button.classList.remove('collapsed');
  }
}

/**
 * Show translated content and hide original content
 * @param {string} sectionCode - Code of the section to show translated content
 */
function showTranslated(sectionCode) {
  const translatedContent = document.getElementById(`translated-content-${sectionCode}`);
  const originalContent = document.getElementById(`original-content-${sectionCode}`);

  if (translatedContent && originalContent) {
    translatedContent.classList.remove('d-none');
    originalContent.classList.add('d-none');
  }
}

/**
 * Show original content and hide translated content
 * @param {string} sectionCode - Code of the section to show original content
 */
function showOriginal(sectionCode) {
  const translatedContent = document.getElementById(`translated-content-${sectionCode}`);
  const originalContent = document.getElementById(`original-content-${sectionCode}`);

  if (translatedContent && originalContent) {
    translatedContent.classList.add('d-none');
    originalContent.classList.remove('d-none');
  }
}

/**
 * Initialize clinical accordion functionality
 * Sets up expand/collapse all buttons
 */
function initializeClinicalAccordion() {
  // Expand All functionality
  const expandAllBtn = document.getElementById('expandAllClinical');
  if (expandAllBtn) {
    expandAllBtn.addEventListener('click', function () {
      document.querySelectorAll('.accordion-collapse').forEach(function (section) {
        section.classList.add('show');
      });
      document.querySelectorAll('.accordion-button').forEach(function (button) {
        button.setAttribute('aria-expanded', 'true');
        button.classList.remove('collapsed');
      });
    });
  }

  // Collapse All functionality
  const collapseAllBtn = document.getElementById('collapseAllClinical');
  if (collapseAllBtn) {
    collapseAllBtn.addEventListener('click', function () {
      document.querySelectorAll('.accordion-collapse').forEach(function (section) {
        section.classList.remove('show');
      });
      document.querySelectorAll('.accordion-button').forEach(function (button) {
        button.setAttribute('aria-expanded', 'false');
        button.classList.add('collapsed');
      });
    });
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializePatientData);
