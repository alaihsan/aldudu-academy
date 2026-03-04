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
        if (container) {
            container.insertAdjacentHTML('beforeend', html);
            // Process the new HTML with HTMX to ensure listeners are bound
            htmx.process(container);
            showSaveIndicator();
        }
    });
}

function publishQuiz() {
    const quizId = document.querySelector('[data-quiz-id]')?.dataset.quizId;
    if (!quizId) return;

    fetch(`/api/quiz/${quizId}/publish`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            window.location.reload();
        }
    });
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
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
        showSaveIndicator();
    }
});

// Re-init HTMX on elements if needed after swap
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Scroll to new question if added
    if (evt.detail.elt.id.startsWith('question-')) {
        evt.detail.elt.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
