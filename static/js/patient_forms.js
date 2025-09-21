/**
 * Patient Forms JavaScript
 * Handles patient form functionality and CDA bilingual display
 */

// Patient Form URL Parameter Population
function initializePatientForm() {
    // Pre-populate form from URL parameters (for test patient links)
    const urlParams = new URLSearchParams(window.location.search);
    const country = urlParams.get('country');
    const patientId = urlParams.get('patient_id');

    if (country) {
        const countryField = document.getElementById('id_country_code');
        if (countryField) {
            countryField.value = country;
        }
    }

    if (patientId) {
        const patientIdField = document.getElementById('id_patient_id');
        if (patientIdField) {
            patientIdField.value = patientId;
        }
    }

    // If both parameters are present, show a helpful message
    if (country && patientId) {
        const existingMessages = document.querySelector('.messages-container');
        if (!existingMessages) {
            const form = document.querySelector('.patient-form-wrapper');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'messages-container';
            messageDiv.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    Form pre-populated with test patient data. Click "Query Patient Documents" to proceed.
                </div>
            `;
            form.insertBefore(messageDiv, form.firstChild);
        }
    }
}

// CDA Bilingual Display Functions
function showBilingual() {
    document.getElementById('bilingual-container').style.gridTemplateColumns = '1fr 1fr';
    document.querySelector('.original-column').style.display = 'block';
    document.querySelector('.translated-column').style.display = 'block';
    updateActiveButton(0);
}

function showOriginal() {
    document.getElementById('bilingual-container').style.gridTemplateColumns = '1fr';
    document.querySelector('.original-column').style.display = 'block';
    document.querySelector('.translated-column').style.display = 'none';
    updateActiveButton(1);
}

function showTranslated() {
    document.getElementById('bilingual-container').style.gridTemplateColumns = '1fr';
    document.querySelector('.original-column').style.display = 'none';
    document.querySelector('.translated-column').style.display = 'block';
    updateActiveButton(2);
}

function updateActiveButton(activeIndex) {
    const buttons = document.querySelectorAll('.toggle-btn');
    buttons.forEach((btn, index) => {
        if (index === activeIndex) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Sync scroll between columns for bilingual display
function initializeBilingualScrollSync() {
    const originalContent = document.querySelector('.original-column .section-content');
    const translatedContent = document.querySelector('.translated-column .section-content');

    if (!originalContent || !translatedContent) return;

    let isScrolling = false;

    originalContent.addEventListener('scroll', function () {
        if (!isScrolling) {
            isScrolling = true;
            translatedContent.scrollTop = originalContent.scrollTop;
            setTimeout(() => isScrolling = false, 50);
        }
    });

    translatedContent.addEventListener('scroll', function () {
        if (!isScrolling) {
            isScrolling = true;
            originalContent.scrollTop = translatedContent.scrollTop;
            setTimeout(() => isScrolling = false, 50);
        }
    });
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function () {
    console.log('🔧 Initializing Patient Forms functionality...');

    // Initialize patient form URL population
    initializePatientForm();

    // Initialize bilingual scroll sync if elements exist
    initializeBilingualScrollSync();

    // Initialize document request form if elements exist
    initializeDocumentRequestForm();

    console.log('✅ Patient Forms initialized successfully');
});

// Make bilingual functions globally available for template usage
window.showBilingual = showBilingual;
window.showOriginal = showOriginal;
window.showTranslated = showTranslated;

// Document Request Form Functionality
function initializeDocumentRequestForm() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Show descriptions for selected options
    const documentTypeField = document.getElementById('document_type');
    if (documentTypeField) {
        documentTypeField.addEventListener('change', function () {
            const selectedOption = this.options[this.selectedIndex];
            const description = selectedOption.getAttribute('data-description');
            const descriptionEl = document.getElementById('document-description');
            if (descriptionEl) {
                descriptionEl.textContent = description || '';
            }
        });
    }

    const consentMethodField = document.getElementById('consent_method');
    if (consentMethodField) {
        consentMethodField.addEventListener('change', function () {
            const selectedOption = this.options[this.selectedIndex];
            const description = selectedOption.getAttribute('data-description');
            const descriptionEl = document.getElementById('consent-description');
            if (descriptionEl) {
                descriptionEl.textContent = description || '';
            }
        });
    }
}
