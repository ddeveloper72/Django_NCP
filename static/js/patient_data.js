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
        if (tab) tab.style.display = 'none';
    });

    // Remove active class from all tab buttons in this section
    const tabButtons = extendedContainer.querySelectorAll('.nav-pills .nav-link');
    tabButtons.forEach(btn => btn.classList.remove('active'));

    // Show the selected tab
    const targetTab = document.getElementById(sectionId + '_' + tabType);
    if (targetTab) {
        targetTab.style.display = 'block';
        console.log('✅ Extended tab shown:', sectionId + '_' + tabType);
    }

    // Activate the corresponding tab button
    const activeButton = extendedContainer.querySelector(`[onclick*="${tabType}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
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
 * Initialize all patient data functionality
 * Called when DOM is ready
 */
function initializePatientData() {
    toggleBreakGlassReason();
    initializeDateFormatting();
    initializeFileUpload();
    initializeBreakGlassModal();
    initializeORCD();
    initializeClinicalAccordion();
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
