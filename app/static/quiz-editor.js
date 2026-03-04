/**
 * Aldudu Academy - Quiz Editor JS
 * Google Forms-style interactions
 */

function addQuestion(type = 'MULTIPLE_CHOICE') {
    const quizId = document.querySelector('[data-quiz-id]')?.dataset.quizId;
    if (!quizId) return;

    const formData = new FormData();
    formData.append('question_type', type);

    fetch(`/api/quiz/${quizId}/question/add`, {
        method: 'POST',
        body: formData
    })
    .then(res => res.text())
    .then(html => {
        const container = document.getElementById('questions-list');
        container.insertAdjacentHTML('beforeend', html);
        // HTMX will handle the new elements
        showSaveIndicator();
    });
}

function publishQuiz() {
    // Everything is autosaved via HTMX blur/change
    // This button can just show a success or redirect
    alert('Seluruh perubahan telah disimpan secara otomatis.');
    window.location.reload();
}

function showSaveIndicator() {
    const indicator = document.getElementById('save-indicator');
    if (!indicator) return;
    
    indicator.classList.remove('opacity-0');
    indicator.classList.add('opacity-100');
    
    setTimeout(() => {
        indicator.classList.remove('opacity-100');
        indicator.classList.add('opacity-0');
    }, 2000);
}

// Global HTMX Event Listeners for Quiz Editor
document.body.addEventListener('htmx:beforeRequest', function() {
    // Show a small saving state if needed
});

document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
        showSaveIndicator();
    } else {
        console.error('HTMX Request failed', evt.detail);
    }
});

// Auto-focus new inputs if added
document.body.addEventListener('htmx:afterSwap', function(evt) {
    const newInputs = evt.detail.elt.querySelectorAll('input[type="text"]');
    if (newInputs.length > 0) {
        newInputs[newInputs.length - 1].focus();
    }
});
