/**
 * Aldudu Academy - Quiz Editor JS
 * Google Forms-style interactions
 */

function publishQuiz() {
    const quizId = document.querySelector('[data-quiz-id]')?.dataset.quizId;
    if (!quizId) return;

    fetch(`/api/quiz/${quizId}/publish`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showSaveIndicator();
            setTimeout(() => {
                alert("Kuis telah dipublikasikan!");
            }, 500);
        }
    });
}

function showSaveIndicator() {
    const indicator = document.getElementById('save-indicator');
    if (!indicator) return;
    
    indicator.classList.add('show');
    
    setTimeout(() => {
        indicator.classList.remove('show');
    }, 2500);
}

// Global HTMX Event Listeners for Quiz Editor
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
        showSaveIndicator();
        
        // If the navbar name needs updating
        const nameInput = document.querySelector('input[name="name"]');
        const navbarName = document.getElementById('navbar-quiz-name');
        if (nameInput && navbarName) {
            navbarName.textContent = nameInput.value;
        }
    }
});

// Re-init logic after HTMX swaps if needed
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.elt.id.startsWith('question-')) {
        // evt.detail.elt.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
