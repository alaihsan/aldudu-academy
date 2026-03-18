/**
 * Aldudu Academy - Quiz Editor JS
 * Handles HTMX events, question deletion via Alpine.js events, and auto-expand
 */

// Global helper to dispatch save toast (used by Alpine and HTMX)
function showSaveIndicator() {
    window.dispatchEvent(new Event('show-save-toast'));
}

// Delete question via Alpine.js event dispatch
function confirmDeleteQuestion(id) {
    window.dispatchEvent(new CustomEvent('open-delete-question', { detail: { id: id } }));
}

function autoExpandTextareas() {
    document.querySelectorAll('.auto-expand').forEach(el => {
        el.style.height = 'auto';
        el.style.height = el.scrollHeight + 'px';
    });
}

// HTMX listeners
document.body.addEventListener('htmx:afterRequest', (evt) => { if (evt.detail.successful) showSaveIndicator(); });
document.body.addEventListener('htmx:afterSwap', () => { autoExpandTextareas(); });

document.addEventListener('DOMContentLoaded', () => { autoExpandTextareas(); });
