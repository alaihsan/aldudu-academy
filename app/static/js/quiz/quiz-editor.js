/**
 * Aldudu Academy - Quiz Editor JS
 */

function publishQuiz() {
    const quizId = document.querySelector('[data-quiz-id]')?.dataset.quizId;
    if (!quizId) return;
    fetch(`/api/quiz/${quizId}/publish`, { method: 'POST' }).then(res => res.json()).then(data => {
        if (data.success) { showSaveIndicator(); setTimeout(() => { alert("Kuis telah dipublikasikan!"); }, 500); }
    });
}

function showSaveIndicator() {
    const indicator = document.getElementById('save-indicator');
    if (!indicator) return;
    if (window.saveToastTimer) clearTimeout(window.saveToastTimer);
    indicator.classList.add('show');
    window.saveToastTimer = setTimeout(() => { indicator.classList.remove('show'); }, 3000);
}

let questionToDelete = null;
function confirmDeleteQuestion(id) { questionToDelete = id; document.getElementById('delete-q-modal')?.classList.remove('hidden'); }
function closeDeleteQModal() { document.getElementById('delete-q-modal')?.classList.add('hidden'); questionToDelete = null; }
async function handleDeleteQuestion() {
    if (!questionToDelete) return;
    try {
        const res = await fetch(`/api/question/${questionToDelete}/delete`, { method: 'DELETE' });
        if (res.ok) { document.getElementById(`question-${questionToDelete}`)?.remove(); closeDeleteQModal(); showSaveIndicator(); }
    } catch (err) { console.error(err); }
}

function autoExpandTextareas() {
    document.querySelectorAll('.auto-expand').forEach(el => {
        el.style.height = 'auto';
        el.style.height = el.scrollHeight + 'px';
    });
}

// HTMX listeners
document.body.addEventListener('htmx:afterRequest', (evt) => { if (evt.detail.successful) showSaveIndicator(); });
document.body.addEventListener('htmx:afterSwap', (evt) => { 
    autoExpandTextareas(); 
    // Re-init dropdowns if needed
});

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('confirm-delete-q-btn')?.addEventListener('click', handleDeleteQuestion);
    autoExpandTextareas();
});
