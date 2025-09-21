/**
 * Document Viewer JavaScript
 * Handles document translation and language switching functionality
 */

// Document Translation Functionality
function initializeDocumentTranslation() {
    const translateButton = document.getElementById('translate_document');
    if (!translateButton) return;

    translateButton.addEventListener('click', function () {
        const targetLanguage = document.getElementById('target_language').value;
        const button = this;
        const originalText = button.innerHTML;

        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Translating...';
        button.disabled = true;

        // Find translatable sections
        const sections = document.querySelectorAll('.cda-section-content, .fhir-resource');
        let translationsCompleted = 0;

        sections.forEach(function (section) {
            const text = section.textContent.trim();
            if (text.length > 20) { // Only translate substantial content

                fetch(window.documentViewerConfig?.translateUrl || '/patient_data/translate_document_section/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': window.documentViewerConfig?.csrfToken || getCsrfToken()
                    },
                    body: JSON.stringify({
                        text: text,
                        target_language: targetLanguage
                    })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.translated_text) {
                            // Store original text if not already stored
                            if (!section.dataset.originalText) {
                                section.dataset.originalText = section.innerHTML;
                            }

                            // Create translation notice
                            const translationNotice = `
                            <div class="alert alert-info alert-sm mb-2">
                                <small><i class="fas fa-language"></i> Translated to ${targetLanguage.toUpperCase()}</small>
                            </div>
                        `;

                            section.innerHTML = translationNotice + data.translated_text;
                        }
                    })
                    .catch(error => {
                        console.error('Translation error:', error);
                    })
                    .finally(() => {
                        translationsCompleted++;
                        if (translationsCompleted === sections.length) {
                            button.innerHTML = originalText;
                            button.disabled = false;
                        }
                    });
            } else {
                translationsCompleted++;
                if (translationsCompleted === sections.length) {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }
            }
        });

        if (sections.length === 0) {
            button.innerHTML = originalText;
            button.disabled = false;
            alert('No translatable content found in this document.');
        }
    });
}

// Language Tab Switching for Uploaded Documents
function showLanguage(sectionIndex, language) {
    // Hide all language content for this section
    const originalContent = document.getElementById(`section-${sectionIndex}-original`);
    const translatedContent = document.getElementById(`section-${sectionIndex}-translated`);

    // Update content visibility
    if (language === 'original') {
        originalContent.classList.add('active');
        translatedContent.classList.remove('active');
    } else {
        originalContent.classList.remove('active');
        translatedContent.classList.add('active');
    }

    // Update tab buttons
    const sectionCard = originalContent.closest('.section-card');
    const buttons = sectionCard.querySelectorAll('.tab-button');
    buttons.forEach((btn, index) => {
        if ((index === 0 && language === 'original') || (index === 1 && language === 'translated')) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Utility function to get CSRF token
function getCsrfToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function () {
    console.log('🔍 Initializing Document Viewer functionality...');

    // Initialize translation functionality
    initializeDocumentTranslation();

    console.log('✅ Document Viewer initialized successfully');
});

// Make showLanguage globally available for template usage
window.showLanguage = showLanguage;
