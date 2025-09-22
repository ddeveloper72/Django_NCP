/**
 * Document List JavaScript
 * Handles SMP document list functionality including deletion and search
 */

// Get CSRF token from cookie utility
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Document deletion functionality
function deleteDocument(documentId, deleteUrl) {
    if (confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
        fetch(deleteUrl.replace('0', documentId), {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error deleting document: ' + data.error);
                }
            })
            .catch(error => {
                alert('Network error: ' + error.message);
            });
    }
}

// Initialize document list functionality
document.addEventListener('DOMContentLoaded', function () {
    console.log('📄 Initializing Document List functionality...');

    // Set up document search functionality
    const searchInput = document.getElementById('document-search');
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            const searchTerm = e.target.value.toLowerCase();
            const documentCards = document.querySelectorAll('.document-card');

            documentCards.forEach(card => {
                const title = card.querySelector('.document-title').textContent.toLowerCase();
                const serviceId = card.querySelector('.meta-value').textContent.toLowerCase();

                if (title.includes(searchTerm) || serviceId.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Set up delete button event listeners
    const deleteButtons = document.querySelectorAll('[data-delete-document]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const documentId = this.dataset.deleteDocument;
            const deleteUrl = this.dataset.deleteUrl;
            deleteDocument(documentId, deleteUrl);
        });
    });

    console.log('✅ Document List initialized successfully');
});